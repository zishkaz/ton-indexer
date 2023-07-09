"""indexes

Revision ID: 1a488612243d
Revises: 007d16058242
Create Date: 2023-07-09 13:17:46.926891

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1a488612243d'
down_revision = '007d16058242'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index('account_states_index_1', 'account_states', ['hash'], unique=False, postgresql_using='hash')
    op.create_index('account_states_index_2', 'account_states', ['code_hash'], unique=False, postgresql_using='hash')
    op.create_index('blocks_index_1', 'blocks', ['workchain', 'shard', 'seqno'], unique=False, postgresql_using='btree')
    op.create_index('blocks_index_2', 'blocks', ['gen_utime'], unique=False, postgresql_using='btree')
    op.create_index('blocks_index_3', 'blocks', ['mc_block_workchain', 'mc_block_shard', 'mc_block_seqno'], unique=False, postgresql_using='btree')
    op.create_index('jetton_burns_index_1', 'jetton_burns', ['transaction_hash'], unique=False, postgresql_using='hash')
    op.create_index('jetton_burns_index_2', 'jetton_burns', ['owner'], unique=False, postgresql_using='hash')
    op.create_index('jetton_burns_index_3', 'jetton_burns', ['jetton_wallet_address'], unique=False, postgresql_using='hash')
    op.create_index('jetton_masters_index_1', 'jetton_masters', ['address'], unique=False, postgresql_using='hash')
    op.create_index('jetton_masters_index_2', 'jetton_masters', ['admin_address'], unique=False, postgresql_using='hash')
    op.create_index('jetton_masters_index_3', 'jetton_masters', ['code_hash'], unique=False, postgresql_using='hash')
    op.create_index('jetton_transfers_index_1', 'jetton_transfers', ['transaction_hash'], unique=False, postgresql_using='hash')
    op.create_index('jetton_transfers_index_2', 'jetton_transfers', ['source'], unique=False, postgresql_using='hash')
    op.create_index('jetton_transfers_index_3', 'jetton_transfers', ['destination'], unique=False, postgresql_using='hash')
    op.create_index('jetton_transfers_index_4', 'jetton_transfers', ['jetton_wallet_address'], unique=False, postgresql_using='hash')
    op.create_index('jetton_transfers_index_5', 'jetton_transfers', ['response_destination'], unique=False, postgresql_using='hash')
    op.create_index('jetton_wallets_index_1', 'jetton_wallets', ['address'], unique=False, postgresql_using='hash')
    op.create_index('jetton_wallets_index_2', 'jetton_wallets', ['owner'], unique=False, postgresql_using='hash')
    op.create_index('jetton_wallets_index_3', 'jetton_wallets', ['jetton'], unique=False, postgresql_using='hash')
    op.create_index('jetton_wallets_index_4', 'jetton_wallets', ['code_hash'], unique=False, postgresql_using='hash')
    op.create_index('message_contents_index_1', 'message_contents', ['hash'], unique=False, postgresql_using='hash')
    op.create_index('messages_index_1', 'messages', ['hash'], unique=False, postgresql_using='hash')
    op.create_index('messages_index_2', 'messages', ['source'], unique=False, postgresql_using='hash')
    op.create_index('messages_index_3', 'messages', ['destination'], unique=False, postgresql_using='hash')
    op.create_index('messages_index_4', 'messages', ['created_lt'], unique=False, postgresql_using='btree')
    op.create_index('messages_index_5', 'messages', ['created_at'], unique=False, postgresql_using='btree')
    op.create_index('messages_index_6', 'messages', ['body_hash'], unique=False, postgresql_using='hash')
    op.create_index('messages_index_7', 'messages', ['init_state_hash'], unique=False, postgresql_using='hash')
    op.create_index('nft_collections_index_1', 'nft_collections', ['address'], unique=False, postgresql_using='hash')
    op.create_index('nft_collections_index_2', 'nft_collections', ['owner_address'], unique=False, postgresql_using='hash')
    op.create_index('nft_collections_index_3', 'nft_collections', ['code_hash'], unique=False, postgresql_using='hash')
    op.create_index('nft_items_index_1', 'nft_items', ['address'], unique=False, postgresql_using='hash')
    op.create_index('nft_items_index_2', 'nft_items', ['collection_address'], unique=False, postgresql_using='hash')
    op.create_index('nft_items_index_3', 'nft_items', ['owner_address'], unique=False, postgresql_using='hash')
    op.create_index('nft_transfers_index_1', 'nft_transfers', ['transaction_hash'], unique=False, postgresql_using='hash')
    op.create_index('nft_transfers_index_2', 'nft_transfers', ['nft_item_address'], unique=False, postgresql_using='hash')
    op.create_index('nft_transfers_index_3', 'nft_transfers', ['old_owner'], unique=False, postgresql_using='hash')
    op.create_index('nft_transfers_index_4', 'nft_transfers', ['new_owner'], unique=False, postgresql_using='hash')
    op.create_index('transaction_messages_index_1', 'transaction_messages', ['transaction_hash'], unique=False, postgresql_using='hash')
    op.create_index('transaction_messages_index_2', 'transaction_messages', ['message_hash'], unique=False, postgresql_using='hash')
    op.create_index('transactions_index_1', 'transactions', ['block_workchain', 'block_shard', 'block_seqno'], unique=False, postgresql_using='btree')
    op.create_index('transactions_index_2', 'transactions', ['account'], unique=False, postgresql_using='hash')
    op.create_index('transactions_index_3', 'transactions', ['hash'], unique=False, postgresql_using='hash')
    op.create_index('transactions_index_4', 'transactions', ['lt'], unique=False, postgresql_using='btree')
    op.create_index('transactions_index_5', 'transactions', ['account_state_hash_before'], unique=False, postgresql_using='hash')
    op.create_index('transactions_index_6', 'transactions', ['account_state_hash_after'], unique=False, postgresql_using='hash')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('transactions_index_6', table_name='transactions', postgresql_using='hash')
    op.drop_index('transactions_index_5', table_name='transactions', postgresql_using='hash')
    op.drop_index('transactions_index_4', table_name='transactions', postgresql_using='btree')
    op.drop_index('transactions_index_3', table_name='transactions', postgresql_using='hash')
    op.drop_index('transactions_index_2', table_name='transactions', postgresql_using='hash')
    op.drop_index('transactions_index_1', table_name='transactions', postgresql_using='btree')
    op.drop_index('transaction_messages_index_2', table_name='transaction_messages', postgresql_using='hash')
    op.drop_index('transaction_messages_index_1', table_name='transaction_messages', postgresql_using='hash')
    op.drop_index('nft_transfers_index_4', table_name='nft_transfers', postgresql_using='hash')
    op.drop_index('nft_transfers_index_3', table_name='nft_transfers', postgresql_using='hash')
    op.drop_index('nft_transfers_index_2', table_name='nft_transfers', postgresql_using='hash')
    op.drop_index('nft_transfers_index_1', table_name='nft_transfers', postgresql_using='hash')
    op.drop_index('nft_items_index_3', table_name='nft_items', postgresql_using='hash')
    op.drop_index('nft_items_index_2', table_name='nft_items', postgresql_using='hash')
    op.drop_index('nft_items_index_1', table_name='nft_items', postgresql_using='hash')
    op.drop_index('nft_collections_index_3', table_name='nft_collections', postgresql_using='hash')
    op.drop_index('nft_collections_index_2', table_name='nft_collections', postgresql_using='hash')
    op.drop_index('nft_collections_index_1', table_name='nft_collections', postgresql_using='hash')
    op.drop_index('messages_index_7', table_name='messages', postgresql_using='hash')
    op.drop_index('messages_index_6', table_name='messages', postgresql_using='hash')
    op.drop_index('messages_index_5', table_name='messages', postgresql_using='btree')
    op.drop_index('messages_index_4', table_name='messages', postgresql_using='btree')
    op.drop_index('messages_index_3', table_name='messages', postgresql_using='hash')
    op.drop_index('messages_index_2', table_name='messages', postgresql_using='hash')
    op.drop_index('messages_index_1', table_name='messages', postgresql_using='hash')
    op.drop_index('message_contents_index_1', table_name='message_contents', postgresql_using='hash')
    op.drop_index('jetton_wallets_index_4', table_name='jetton_wallets', postgresql_using='hash')
    op.drop_index('jetton_wallets_index_3', table_name='jetton_wallets', postgresql_using='hash')
    op.drop_index('jetton_wallets_index_2', table_name='jetton_wallets', postgresql_using='hash')
    op.drop_index('jetton_wallets_index_1', table_name='jetton_wallets', postgresql_using='hash')
    op.drop_index('jetton_transfers_index_5', table_name='jetton_transfers', postgresql_using='hash')
    op.drop_index('jetton_transfers_index_4', table_name='jetton_transfers', postgresql_using='hash')
    op.drop_index('jetton_transfers_index_3', table_name='jetton_transfers', postgresql_using='hash')
    op.drop_index('jetton_transfers_index_2', table_name='jetton_transfers', postgresql_using='hash')
    op.drop_index('jetton_transfers_index_1', table_name='jetton_transfers', postgresql_using='hash')
    op.drop_index('jetton_masters_index_3', table_name='jetton_masters', postgresql_using='hash')
    op.drop_index('jetton_masters_index_2', table_name='jetton_masters', postgresql_using='hash')
    op.drop_index('jetton_masters_index_1', table_name='jetton_masters', postgresql_using='hash')
    op.drop_index('jetton_burns_index_3', table_name='jetton_burns', postgresql_using='hash')
    op.drop_index('jetton_burns_index_2', table_name='jetton_burns', postgresql_using='hash')
    op.drop_index('jetton_burns_index_1', table_name='jetton_burns', postgresql_using='hash')
    op.drop_index('blocks_index_3', table_name='blocks', postgresql_using='btree')
    op.drop_index('blocks_index_2', table_name='blocks', postgresql_using='btree')
    op.drop_index('blocks_index_1', table_name='blocks', postgresql_using='btree')
    op.drop_index('account_states_index_2', table_name='account_states', postgresql_using='hash')
    op.drop_index('account_states_index_1', table_name='account_states', postgresql_using='hash')
    # ### end Alembic commands ###
