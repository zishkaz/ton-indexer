from __future__ import annotations
from typing import Annotated, List, Optional, Dict, Any
from sqlalchemy.orm import sessionmaker

from sqlalchemy import (
    String,
    Integer,
    BigInteger,
    Boolean,
    Index,
    Enum,
    Numeric,
    Column,
)
from sqlalchemy.schema import ForeignKeyConstraint
from sqlalchemy import ForeignKey, Table
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Session

# from sqlalchemy.future import select

from sqlalchemy.dialects.postgresql import JSONB

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import create_engine

from indexer.core.settings import Settings


MASTERCHAIN_INDEX = -1
MASTERCHAIN_SHARD = -9223372036854775808

settings = Settings()


# SQL Alchemy Engines
# async engine
def get_async_engine(settings: Settings):
    engine = create_async_engine(
        settings.pg_dsn, pool_size=128, max_overflow=24, pool_timeout=128, echo=True
    )
    return engine


# sync engine
def get_sync_engine(settings: Settings):
    dsn = settings.pg_dsn.replace("+asyncpg", "+psycopg2")
    engine = create_engine(
        dsn, pool_size=128, max_overflow=24, pool_timeout=128, echo=True
    )
    return engine


async_engine = get_async_engine(settings)
AsyncSessionMaker = sessionmaker(bind=async_engine, class_=AsyncSession)

sync_engine = get_sync_engine(settings)
SyncSessionMaker = sessionmaker(bind=sync_engine)


# database
class Base(DeclarativeBase):
    __allow_unmapped__ = False


# types
AccountStatusType = Enum(
    "uninit", "frozen", "active", "nonexist", name="account_status_type"
)
str44 = Annotated[str, mapped_column(String(44))]
str44opt = Annotated[str, mapped_column(String(44), nullable=True)]


# classes
class Block(Base):
    __tablename__ = "blocks"
    __table_args__ = (
        ForeignKeyConstraint(
            ["mc_block_workchain", "mc_block_shard", "mc_block_seqno"],
            ["blocks.workchain", "blocks.shard", "blocks.seqno"]
        ),
    )

    workchain: Mapped[int] = mapped_column(Integer, primary_key=True)
    shard: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    seqno: Mapped[int] = mapped_column(Integer, primary_key=True)
    root_hash: Mapped[str44]
    file_hash: Mapped[str44]

    mc_block_workchain: int = Column(Integer, nullable=True)
    mc_block_shard: str = Column(BigInteger, nullable=True)
    mc_block_seqno: int = Column(Integer, nullable=True)

    masterchain_block: Mapped[Block] = relationship(
        "Block", 
        remote_side=[workchain, shard, seqno], 
        back_populates='shard_blocks'
    )
    shard_blocks: Mapped[List[Block]] = relationship(
        "Block", back_populates="masterchain_block"
    )

    global_id: Mapped[int] = mapped_column(Integer)
    version: Mapped[int] = mapped_column(Integer)
    after_merge: Mapped[bool] = mapped_column(Boolean)
    before_split: Mapped[bool] = mapped_column(Boolean)
    after_split: Mapped[bool] = mapped_column(Boolean)
    want_split: Mapped[bool] = mapped_column(Boolean)
    key_block: Mapped[bool] = mapped_column(Boolean)
    vert_seqno_incr: Mapped[bool] = mapped_column(Boolean)
    flags: Mapped[int] = mapped_column(Integer)
    gen_utime: Mapped[int] = mapped_column(BigInteger)
    start_lt: Mapped[int] = mapped_column(BigInteger)
    end_lt: Mapped[int] = mapped_column(BigInteger)
    validator_list_hash_short: Mapped[int] = mapped_column(Integer)
    gen_catchain_seqno: Mapped[int] = mapped_column(Integer)
    min_ref_mc_seqno: Mapped[int] = mapped_column(Integer)
    prev_key_block_seqno: Mapped[int] = mapped_column(Integer)
    vert_seqno: Mapped[int] = mapped_column(Integer)
    master_ref_seqno: Mapped[int] = mapped_column(Integer, nullable=True)
    rand_seed: Mapped[str44]
    created_by: Mapped[str] = mapped_column(String)

    tx_count: Mapped[int] = mapped_column(Integer)

    transactions = relationship("Transaction", back_populates="block")


class Trace(Base):
    __tablename__ = "traces"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    meta: Mapped[Dict[str, Any]] = mapped_column(JSONB)

    # transactions: List["TranceTransactions"] = relationship("TraceTransaction", back_populates="trace")
    transactions: Mapped[List[Transaction]] = relationship(
        "Transaction",
        primaryjoin="Trace.id == foreign(Transaction.trace_id)",
        # back_populates="trace",
        uselist=True,
    )
    edges: Mapped[List[TraceEdge]] = relationship("TraceEdge", back_populates="trace")


class TraceEdge(Base):
    __tablename__ = "trace_graph"
    trace_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("traces.id"), primary_key=True
    )
    left_tx_hash: Mapped[str] = mapped_column(String(44), primary_key=True)
    right_tx_hash: Mapped[str] = mapped_column(String(44), primary_key=True)

    trace: Mapped[Trace] = relationship("Trace", back_populates="edges")


class AccountState(Base):
    __tablename__ = "account_states"

    hash: Mapped[str] = mapped_column(String(44), primary_key=True)
    account: Mapped[str] = mapped_column(String)
    balance: Mapped[int] = mapped_column(Numeric)
    account_status: Mapped[str] = mapped_column(AccountStatusType)
    frozen_hash: Mapped[str44opt]
    code_hash: Mapped[str44opt]
    data_hash: Mapped[str44opt]


class LatestAccountState(Base):
    __tablename__ = "latest_account_states"
    account: Mapped[str] = mapped_column(String, primary_key=True)
    hash: Mapped[str44]
    balance: Mapped[int] = mapped_column(Numeric)
    account_status: Mapped[str] = mapped_column(AccountStatusType)
    frozen_hash: Mapped[str44opt]
    code_hash: Mapped[str44opt]
    data_hash: Mapped[str44opt]
    timestamp: Mapped[int] = mapped_column(Integer)
    last_trans_lt: Mapped[int] = mapped_column(BigInteger)


MessageDirectionType = Enum("in", "out", name="message_direction_type")


class TransactionMessage(Base):
    __tablename__ = "transaction_messages"
    transaction_hash: Mapped[str] = mapped_column(
        String(44), ForeignKey("transactions.hash"), primary_key=True
    )
    message_hash: Mapped[str] = mapped_column(String(44), primary_key=True)
    direction: Mapped[str] = mapped_column(MessageDirectionType, primary_key=True)

    transaction: Mapped[Transaction] = relationship(
        "Transaction", 
        back_populates="transaction_messages"
    )
    message: Mapped[Message] = relationship(
        "Message", 
        primaryjoin="foreign(Message.hash) == TransactionMessage.message_hash",
        back_populates="transaction_messages"
    )


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["block_workchain", "block_shard", "block_seqno"],
            ["blocks.workchain", "blocks.shard", "blocks.seqno"],
        ),
    )

    block_workchain: Mapped[int] = mapped_column(Integer)
    block_shard: Mapped[int] = mapped_column(BigInteger)
    block_seqno: Mapped[int] = mapped_column(Integer)
    mc_block_seqno: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    block: Mapped[Block] = relationship("Block", back_populates="transactions")

    account: Mapped[str] = mapped_column(String)
    hash: Mapped[str] = mapped_column(String(44), primary_key=True)
    lt: Mapped[int] = mapped_column(BigInteger)
    prev_trans_hash: Mapped[str] = mapped_column(String(44))
    prev_trans_lt: Mapped[int] = mapped_column(BigInteger)
    now: Mapped[int] = mapped_column(Integer)

    orig_status: Mapped[str] = mapped_column(AccountStatusType)
    end_status: Mapped[str] = mapped_column(AccountStatusType)

    total_fees: Mapped[int] = mapped_column(BigInteger)

    account_state_hash_before: Mapped[str44]
    account_state_hash_after: Mapped[str44]

    trace_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    account_state_before: Mapped[AccountState] = relationship(
        "AccountState",
        primaryjoin="Transaction.account_state_hash_before == foreign(AccountState.hash)",
        viewonly=True,
    )
    account_state_after: Mapped[AccountState] = relationship(
        "AccountState",
        primaryjoin="Transaction.account_state_hash_after == foreign(AccountState.hash)",
        viewonly=True,
    )
    account_state_latest: Mapped[AccountState] = relationship(
        "LatestAccountState",
        primaryjoin="Transaction.account == foreign(LatestAccountState.account)",
        lazy="selectin",
        viewonly=True,
    )
    description: Mapped[Dict[str, Any]] = mapped_column(JSONB)

    in_msg: Mapped[Message] = relationship(
        "Message",
        secondary="transaction_messages",
        primaryjoin="Transaction.hash == foreign(TransactionMessage.transaction_hash)",
        secondaryjoin="and_(foreign(Message.hash) == TransactionMessage.message_hash, TransactionMessage.direction == 'in')",
        back_populates="in_transaction",
        uselist=False,
    )
    out_msgs: Mapped[List[Message]] = relationship(
        "Message",
        secondary="transaction_messages",
        primaryjoin="Transaction.hash == foreign(TransactionMessage.transaction_hash)",
        secondaryjoin="and_(foreign(Message.hash) == TransactionMessage.message_hash, TransactionMessage.direction == 'out')",
        back_populates="out_transaction",
        uselist=True,
    )
    messages: Mapped[List[Message]] = relationship(
        "Message",
        secondary="transaction_messages",
        primaryjoin="Transaction.hash == foreign(TransactionMessage.transaction_hash)",
        secondaryjoin="foreign(Message.hash) == TransactionMessage.message_hash",
        back_populates="out_transaction",
        uselist=True,
    )
    transaction_messages: Mapped[List[TransactionMessage]] = relationship(
        "TransactionMessage", 
        back_populates="transaction",
        uselist=True
    )
    trace: Mapped[Trace] = relationship(
        "Trace",
        primaryjoin="Transaction.trace_id == foreign(Trace.id)",
    )


class MessageContent(Base):
    __tablename__ = "message_contents"

    hash: Mapped[str] = mapped_column(String(44), primary_key=True)
    body: Mapped[str] = mapped_column(String)


class Message(Base):
    __tablename__ = "messages"
    hash: Mapped[str] = mapped_column(String(44), primary_key=True)
    source: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    destination: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    value: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    fwd_fee: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    ihr_fee: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_lt: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    opcode: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ihr_disabled: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    bounce: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    bounced: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    import_fee: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    body_hash: Mapped[Optional[str]] = mapped_column(String(44), nullable=True)
    init_state_hash: Mapped[Optional[str]] = mapped_column(String(44), nullable=True)

    transaction_messages: Mapped[List[TransactionMessage]] = relationship(
        "TransactionMessage", 
        # primaryjoin="Message.hash == foreign(TransactionMessage.message_hash)",
        back_populates="message"
    )
    in_transaction: Mapped[Transaction] = relationship(
        "Transaction", back_populates="in_msg", uselist=False
    )
    out_transaction: Mapped[Transaction] = relationship(
        "Transaction", back_populates="out_msgs", uselist=False
    )

    message_content = relationship(
        "MessageContent", primaryjoin="Message.body_hash == MessageContent.hash", viewonly=True
    )
    init_state = relationship(
        "MessageContent",
        primaryjoin="Message.init_state_hash == MessageContent.hash",
        viewonly=True,
    )

    source_account_state = relationship(
        "LatestAccountState",
        primaryjoin="Message.source == LatestAccountState.account",
        viewonly=True,
    )
    destination_account_state = relationship(
        "LatestAccountState",
        primaryjoin="Message.destination == LatestAccountState.account",
        viewonly=True,
    )


class JettonMaster(Base):
    __tablename__ = "jetton_masters"
    address: Mapped[str] = mapped_column(String, primary_key=True)
    total_supply: Mapped[int] = mapped_column(Numeric)
    mintable: Mapped[bool] = mapped_column(Boolean)
    admin_address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    jetton_content: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=True)
    jetton_wallet_code_hash: Mapped[str] = mapped_column(String(44))
    code_hash: Mapped[str] = mapped_column(String(44))
    code_boc: Mapped[str] = mapped_column(String)
    data_hash: Mapped[str] = mapped_column(String(44))
    data_boc: Mapped[str] = mapped_column(String)
    last_transaction_lt: Mapped[int] = mapped_column(BigInteger)

    wallets: Mapped[List[JettonWallet]] = relationship(
        "JettonWallet", back_populates="jetton_master", uselist=True
    )


class JettonWallet(Base):
    __tablename__ = "jetton_wallets"
    address: Mapped[str] = mapped_column(String, primary_key=True)
    balance: Mapped[int] = mapped_column(Numeric)
    owner: Mapped[str] = mapped_column(String)
    jetton: Mapped[str] = mapped_column(String)
    last_transaction_lt: Mapped[int] = mapped_column(BigInteger)
    code_hash: Mapped[str] = mapped_column(String(44))
    data_hash: Mapped[str] = mapped_column(String(44))

    transfers: Mapped[List[JettonTransfer]] = relationship(
        "JettonTransfer",
        primaryjoin="JettonWallet.address == JettonTransfer.jetton_wallet_address",
        back_populates="jetton_wallet",
        uselist=True,
    )
    burns: Mapped[List[JettonBurn]] = relationship(
        "JettonBurn",
        primaryjoin="JettonWallet.address == JettonBurn.jetton_wallet_address",
        back_populates="jetton_wallet",
        uselist=True,
    )

    jetton_master: Mapped[JettonMaster] = relationship(
        "JettonMaster", primaryjoin="JettonWallet.jetton == JettonMaster.address", uselist=False
    )


class JettonTransfer(Base):
    __tablename__ = "jetton_transfers"
    transaction_hash: Mapped[str] = mapped_column(
        String, ForeignKey("transactions.hash"), primary_key=True
    )
    query_id: Mapped[int] = mapped_column(Numeric)
    amount: Mapped[int] = mapped_column(Numeric)
    source: Mapped[str] = mapped_column(String)
    destination: Mapped[str] = mapped_column(String)
    jetton_wallet_address: Mapped[str] = mapped_column(String)
    response_destination: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    custom_payload: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    forward_ton_amount: Mapped[Optional[int]] = mapped_column(Numeric, nullable=True)
    forward_payload: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    transaction: Mapped[Transaction] = relationship("Transaction")
    jetton_wallet: Mapped[JettonWallet] = relationship(
        "JettonWallet", back_populates="transfers", uselist=False
    )


class JettonBurn(Base):
    __tablename__ = "jetton_burns"
    transaction_hash: Mapped[str] = mapped_column(
        String, ForeignKey("transactions.hash"), primary_key=True
    )
    query_id: Mapped[int] = mapped_column(Numeric)
    owner: Mapped[str] = mapped_column(String)
    amount: Mapped[int] = mapped_column(Numeric)
    jetton_wallet_address: Mapped[str] = mapped_column(String)
    response_destination: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    custom_payload: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    transaction: Mapped[Transaction] = relationship("Transaction")
    jetton_wallet: Mapped[JettonWallet] = relationship(
        "JettonWallet", back_populates="burns", uselist=False
    )


class NFTCollection(Base):
    __tablename__ = "nft_collections"
    address: Mapped[str] = mapped_column(String, primary_key=True)
    next_item_index: Mapped[int] = mapped_column(Numeric)
    owner_address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    collection_content: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=True)
    code_hash: Mapped[str] = mapped_column(String(44))
    code_boc: Mapped[str] = mapped_column(String)
    data_hash: Mapped[str] = mapped_column(String(44))
    data_boc: Mapped[str] = mapped_column(String)
    last_transaction_lt: Mapped[int] = mapped_column(BigInteger)

    items: Mapped[List[NFTItem]] = relationship(
        "NFTItem", back_populates="collection", uselist=True
    )


class NFTItem(Base):
    __tablename__ = "nft_items"
    address: Mapped[str] = mapped_column(String, primary_key=True)
    init: Mapped[bool] = mapped_column(Boolean)
    index: Mapped[int] = mapped_column(Numeric)
    collection_address: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )  # TODO: index
    owner_address: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )  # TODO: index
    content: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=True)
    last_transaction_lt: Mapped[int] = mapped_column(BigInteger)
    code_hash: Mapped[str] = mapped_column(String(44))
    data_hash: Mapped[str] = mapped_column(String(44))

    collection: Mapped[Optional[NFTCollection]] = relationship(
        "NFTCollection",
        primaryjoin="NFTItem.collection_address == NFTCollection.address",
        back_populates="items",
        uselist=False,
    )

    transfers: Mapped[List[NFTTransfer]] = relationship(
        "NFTTransfer",
        primaryjoin="NFTItem.address == NFTTransfer.nft_item_address",
        uselist=True,
    )


class NFTTransfer(Base):
    __tablename__ = "nft_transfers"
    transaction_hash: Mapped[str] = mapped_column(
        String, ForeignKey("transactions.hash"), primary_key=True
    )
    query_id: Mapped[int] = mapped_column(Numeric)
    nft_item_address: Mapped[str] = mapped_column(String)  # TODO: index
    old_owner: Mapped[str] = mapped_column(String)  # TODO: index
    new_owner: Mapped[str] = mapped_column(String)  # TODO: index
    response_destination: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    custom_payload: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    forward_amount: Mapped[int] = mapped_column(Numeric)
    forward_payload: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    transaction: Mapped[Transaction] = relationship("Transaction")
    nft_item: Mapped[NFTItem] = relationship(
        "NFTItem", back_populates="transfers", uselist=False
    )


# # Indexes
# # Index("blocks_index_1", Block.workchain, Block.shard, Block.seqno)
# Index("blocks_index_2", Block.gen_utime)
# Index("blocks_index_3", Block.mc_block_workchain, Block.mc_block_shard, Block.mc_block_seqno)

# Index("transactions_index_1", Transaction.block_workchain, Transaction.block_shard, Transaction.block_seqno)
# Index("transactions_index_2", Transaction.account)
# # Index("transactions_index_3", Transaction.hash)
# Index("transactions_index_3", Transaction.now)
# Index("transactions_index_4", Transaction.lt)
# Index("transactions_index_6", Transaction.trace_id)

# # Index('account_states_index_1', AccountState.hash)
# # Index('account_states_index_2', AccountState.code_hash)

# # Index("messages_index_1", Message.hash)
# Index("messages_index_2", Message.source)
# Index("messages_index_3", Message.destination)
# Index("messages_index_4", Message.created_lt)
# # Index("messages_index_5", Message.created_at)
# # Index("messages_index_6", Message.body_hash)
# # Index("messages_index_7", Message.init_state_hash)

# # Index("transaction_messages_index_1", TransactionMessage.transaction_hash)
# Index("transaction_messages_index_2", TransactionMessage.message_hash)

# # Index("message_contents_index_1", MessageContent.hash)

# # Index("jetton_wallets_index_1", JettonWallet.address)
# Index("jetton_wallets_index_2", JettonWallet.owner)
# Index("jetton_wallets_index_3", JettonWallet.jetton)
# # Index("jetton_wallets_index_4", JettonWallet.code_hash)

# # Index("jetton_masters_index_1", JettonMaster.address)
# Index("jetton_masters_index_2", JettonMaster.admin_address)
# # Index("jetton_masters_index_3", JettonMaster.code_hash)

# # Index("jetton_transfers_index_1", JettonTransfer.transaction_hash)
# Index("jetton_transfers_index_2", JettonTransfer.source)
# Index("jetton_transfers_index_3", JettonTransfer.destination)
# Index("jetton_transfers_index_4", JettonTransfer.jetton_wallet_address)
# # Index("jetton_transfers_index_5", JettonTransfer.response_destination)

# # Index("jetton_burns_index_1", JettonBurn.transaction_hash)
# Index("jetton_burns_index_2", JettonBurn.owner)
# Index("jetton_burns_index_3", JettonBurn.jetton_wallet_address)

# # Index("nft_collections_index_1", NFTCollection.address)
# Index("nft_collections_index_2", NFTCollection.owner_address)
# # Index("nft_collections_index_3", NFTCollection.code_hash)

# # Index("nft_items_index_1", NFTItem.address)
# Index("nft_items_index_2", NFTItem.collection_address)
# Index("nft_items_index_3", NFTItem.owner_address)

# # Index("nft_transfers_index_1", NFTTransfer.transaction_hash)
# Index("nft_transfers_index_2", NFTTransfer.nft_item_address)
# Index("nft_transfers_index_3", NFTTransfer.old_owner)
# Index("nft_transfers_index_4", NFTTransfer.new_owner)


# # # trace indexes
# # Index("trace_transaction_index_1", TraceTransaction.tx_hash)
# Index("even_detector__transaction_index_1", Transaction.lt.asc(), postgresql_where=(Transaction.trace_id.is_(None)))
