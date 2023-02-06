import argparse
import asyncio
import time
import sys
import traceback

from asgiref.sync import sync_to_async
from collections import deque

from pytonlib import LiteServerTimeout, BlockDeleted

from indexer.core.celery import app
from indexer.core.tasks import get_block, get_last_mc_block
from indexer.core.database import init_database, SessionMaker
from indexer.core.crud import get_existing_seqnos_between_interval
from indexer.core.settings import Settings
from loguru import logger


settings = Settings()

def wait_for_broker_connection():
    while True:
        try:
            app.broker_connection().ensure_connection(max_retries=3)
        except Exception:
            logger.warning(f"Can't connect to celery broker. Trying again...")
            time.sleep(3)
            continue
        logger.info(f"Connected to celery broker.")
        break

async def asyncify(celery_task, *args, **kwargs):
    delay = 0.1
    celery_result = await sync_to_async(celery_task.apply_async)(*args, **kwargs)
    while not celery_result.ready():
        await asyncio.sleep(delay)
        delay = min(delay * 1.5, 1)  # exponential backoff, max 1 second
    return celery_result


class Meter:
    def __init__(self, use_time=False):
        self.start_time = 0
        self.count = 0
        self.init = False
        
    def hit(self, count=1, elapsed=None):
        self.count += count
        if not self.init:
            self.reset()

    def reset(self):
        self.start_time = time.time()
        self.count = 0
        self.init = True
        
    @property
    def tps(self):
        return self.count / (time.time() - self.start_time)

class IndexScheduler:
    def __init__(self, celery_queue):
        self.celery_queue = celery_queue
        self.seqnos_to_process_queue = deque()
        self.max_parallel_tasks_semaphore = None
        self.running_tasks = set()
        self.is_liteserver_up = None
        self.reschedule_failed_blocks = None
        self.meter = Meter()
        self.priority = 5

    def run(self):
        raise RuntimeError('abstract method')

    async def _not_indexed_seqnos_between(self, low_seqno, high_seqno):
        async with SessionMaker() as session:
            seqnos_already_in_db = await get_existing_seqnos_between_interval(session, low_seqno, high_seqno)
        logger.info(f"{len(seqnos_already_in_db)} seqnos already exist in DB")
        return [seqno for seqno in range(low_seqno, high_seqno + 1) if (seqno,) not in seqnos_already_in_db]

    async def _index_blocks(self, return_on_empty):
        while True:
            try:
                if not self.is_liteserver_up:
                    await asyncio.sleep(1)
                    continue

                chunk = []
                while len(chunk) < settings.blocks_per_task:
                    try:
                        seqno_to_process = self.seqnos_to_process_queue.popleft()
                    except IndexError:
                        if return_on_empty and len(chunk) == 0:
                            return
                        break
                    chunk.append(seqno_to_process)
                if len(chunk) == 0:
                    await asyncio.sleep(0.1)
                    continue

                await self.max_parallel_tasks_semaphore.acquire()
                task = asyncify(get_block, [chunk], serializer='pickle', queue=self.celery_queue, priority=self.priority)
                self.running_tasks.add(self.loop.create_task(task))
            except asyncio.CancelledError:
                logger.warning("Task _index_blocks was cancelled")
                return
            except BaseException as e:
                logger.error("Task _index_blocks raised exception: {exception}", exception=e)

    def handle_get_block_result(self, seqno, seqno_result):
        if seqno_result is None:
            logger.debug("Masterchain block {seqno} was indexed. TPS: {tps}", seqno=seqno, tps=self.meter.tps)
        elif isinstance(seqno_result, LiteServerTimeout):
            logger.critical("Masterchain block {seqno} was not indexed because Lite Server is not responding: {exception}.", 
                seqno=seqno, exception=seqno_result)
            logger.critical("Block {seqno} is rescheduled", seqno=seqno)
            self.seqnos_to_process_queue.appendleft(seqno)
        elif isinstance(seqno_result, BlockDeleted):
            logger.critical("Masterchain block {seqno} was not indexed because Lite Server already deleted this block", seqno=seqno)
            logger.critical("Block {seqno} is skipped", seqno=seqno)
        elif isinstance(seqno_result, BaseException):
            logger.critical("Masterchain block {seqno} was not indexed. Exception of type {exc_type} occured: {exception}", 
                seqno=seqno, exc_type=type(seqno_result).__name__, exception=seqno_result)
            if self.reschedule_failed_blocks:
                logger.critical("Block {seqno} is rescheduled", seqno=seqno)
                self.seqnos_to_process_queue.appendleft(seqno)
            else:
                logger.critical("Block {seqno} is skipped", seqno=seqno)
        else:
            raise RuntimeError(f"Unexpected get_block result type for block {seqno}: {seqno_result}")

    async def _read_results(self):
        while True:
            try:
                done_tasks = set(filter(lambda x: x.done(), self.running_tasks))
                self.running_tasks = set(filter(lambda x: x not in done_tasks, self.running_tasks))
                for task in done_tasks:
                    self.max_parallel_tasks_semaphore.release()
                    async_result = task.result()
                    try:
                        result = async_result.get()
                    except BaseException as e:
                        logger.error("Task {async_result} raised unknown exception: {exception}. Rescheduling the task's chunk.", async_result=async_result, exception=e)
                        self.seqnos_to_process_queue.extendleft(async_result.args[0])
                    else:
                        self.meter.hit(len(result))
                        for (seqno, seqno_result) in result:
                            self.handle_get_block_result(seqno, seqno_result)

                await asyncio.sleep(0.3)
            except asyncio.CancelledError:
                logger.warning("Task _read_results was cancelled")
                return
            except BaseException as e:
                logger.error(f"Task _read_results raised exception: {e}. {traceback.format_exc()}")
    
    async def _check_liteserver_health(self):
        while True:
            try:
                try:
                    last_mc_block_async_result = await asyncify(get_last_mc_block, [], serializer='pickle', queue=self.celery_queue)
                    last_mc_block_async_result.get()
                except LiteServerTimeout:
                    if self.is_liteserver_up or self.is_liteserver_up is None:
                        logger.critical(f"Lite Server is not responding. Pausing indexing until it's not alive.")
                        self.is_liteserver_up = False
                else:
                    if not self.is_liteserver_up:
                        logger.info(f"Lite Server is alive. Starting the indexing.")
                        self.is_liteserver_up = True
                await asyncio.sleep(2)
            except BaseException as e:
                logger.error(f"Task _check_liteserver_health raised exception: {e}. {traceback.format_exc()}")

class BackwardScheduler(IndexScheduler):
    def __init__(self, celery_queue):
        super(BackwardScheduler, self).__init__(celery_queue)
        self.reschedule_failed_blocks = False
    
    def run(self):
        self.loop = asyncio.get_event_loop()
        self.max_parallel_tasks_semaphore = asyncio.Semaphore(settings.max_scheduled_tasks)
        self.loop.run_until_complete(self.schedule_seqnos())
        self.check_liteserver_health_task = self.loop.create_task(self._check_liteserver_health())
        self.index_blocks_task = self.loop.create_task(self._index_blocks(return_on_empty=True))
        self.read_results_task = self.loop.create_task(self._read_results())
        self.loop.run_until_complete(self._wait_finish())

    async def schedule_seqnos(self):
        logger.info(f"Backward scheduler started. From {settings.start_seqno} to {settings.bottom_seqno}.")

        seqnos_to_index = await self._not_indexed_seqnos_between(settings.bottom_seqno, settings.start_seqno)
        seqnos_to_index.reverse()

        self.seqnos_to_process_queue.extend(seqnos_to_index)

    async def _wait_finish(self):
        done, pending = await asyncio.wait([self.check_liteserver_health_task, self.index_blocks_task, self.read_results_task], return_when=asyncio.FIRST_COMPLETED)
        done_task = done.pop()
        if done_task is self.index_blocks_task:
            while len(self.running_tasks) > 0:
                await asyncio.sleep(0.5)
            self.read_results_task.cancel()
            await self.read_results_task
            logger.info('Backward scheduler finished working')
            not_indexed = await self._not_indexed_seqnos_between(settings.bottom_seqno, settings.start_seqno)
            if len(not_indexed) > 0:
                logger.info('Failed to index following seqnos: {seqnos}', seqnos=not_indexed)
            else:
                logger.info('All seqnos were successfully indexed')
        else:
            logger.critical(f"Task {done_task} unexpectedly stopped. Aborting the execution.")
            sys.exit(-1)

class ForwardScheduler(IndexScheduler):
    def __init__(self, celery_queue):
        super(ForwardScheduler, self).__init__(celery_queue)
        self.reschedule_failed_blocks = True
        self.current_seqno = settings.start_seqno + 1
        self.priority = 10
    
    def run(self):
        self.loop = asyncio.get_event_loop()
        self.max_parallel_tasks_semaphore = asyncio.Semaphore(settings.max_scheduled_tasks)
        self.check_liteserver_health_task = self.loop.create_task(self._check_liteserver_health())
        self.get_new_blocks_task = self.loop.create_task(self._get_new_blocks())
        self.index_blocks_task = self.loop.create_task(self._index_blocks(return_on_empty=False))
        self.read_results_task = self.loop.create_task(self._read_results())
        self.meter.reset()
        done, pending = self.loop.run_until_complete(asyncio.wait([self.check_liteserver_health_task, self.get_new_blocks_task, self.index_blocks_task, self.read_results_task], return_when=asyncio.FIRST_COMPLETED))
        logger.critical(f"Task {done.pop()} unexpectedly stopped. Aborting the execution.")
        sys.exit(-1)

    async def _get_new_blocks(self):
        is_first_iteration = True
        while True:
            try:
                if not self.is_liteserver_up:
                    await asyncio.sleep(5)
                    continue

                last_mc_block_async_result = await asyncify(get_last_mc_block, [], serializer='pickle', queue=self.celery_queue)
                last_mc_block = last_mc_block_async_result.get()
                if last_mc_block['seqno'] < self.current_seqno:
                    await asyncio.sleep(0.2)
                    continue
                logger.info("New masterchain block: {seqno}", seqno=last_mc_block['seqno'])

                if is_first_iteration:
                    new_seqnos = await self._not_indexed_seqnos_between(self.current_seqno, last_mc_block['seqno'] + 1)
                    is_first_iteration = False
                else:
                    new_seqnos = range(self.current_seqno, last_mc_block['seqno'] + 1)

                self.seqnos_to_process_queue.extend(new_seqnos)
                
                self.current_seqno = last_mc_block['seqno'] + 1
            except asyncio.CancelledError:
                logger.warning("Task _get_new_blocks was cancelled")
                return
            except BaseException as e:
                logger.error("Task _get_new_blocks raised exception: {exception}", exception=e)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    parser = argparse.ArgumentParser('ton-index scheduler')
    parser.add_argument('-q', '--queue', type=str, default=None, help='Task queue')
    parser.add_argument('-i', '--init', action='store_true', help='Init database')
    parser.add_argument('direction', type=str, choices=['forward', 'backward'], help='Scheduler type')
    args = parser.parse_args()

    if args.queue is None:
        args.queue = args.direction + "_queue"
    
    logger.info('Sleeping 10 seconds before start')
    time.sleep(10)
    init_database(create=args.init)
    wait_for_broker_connection()
    
    if args.direction == 'backward':
        scheduler = BackwardScheduler(args.queue)
    elif args.direction == 'forward':
        scheduler = ForwardScheduler(args.queue)
    
    scheduler.run()

