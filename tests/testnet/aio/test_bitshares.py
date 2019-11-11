# -*- coding: utf-8 -*-
import asyncio
import pytest
import logging

from datetime import datetime
from bitshares.aio.asset import Asset
from bitshares.aio.amount import Amount
from bitshares.aio.price import Price
from bitshares.aio.proposal import Proposals
from bitshares.aio.worker import Workers

log = logging.getLogger("grapheneapi")
log.setLevel(logging.DEBUG)


@pytest.fixture(scope="module")
async def testworker(bitshares, default_account):
    amount = await Amount("1000 TEST")
    end = datetime(2099, 1, 1)
    await bitshares.create_worker("test", amount, end, account=default_account)


@pytest.fixture(scope="module")
async def bitasset(create_asset, default_account):
    await create_asset("CNY", 5, is_bitasset=True)
    asset = await Asset("CNY")
    await asset.update_feed_producers([default_account])


@pytest.mark.asyncio
async def test_aio_chain_props(bitshares):
    """ Test chain properties
    """
    # Wait for several blcocks
    await asyncio.sleep(3)
    props = await bitshares.info()
    assert isinstance(props, dict)
    assert props["head_block_number"] > 0


@pytest.mark.asyncio
async def test_transfer(bitshares, default_account):
    await bitshares.transfer("init1", 10, "TEST", memo="xxx", account=default_account)


@pytest.mark.asyncio
async def test_create_account(bitshares, default_account):
    await bitshares.create_account(
        "foobar", referrer=default_account, registrar=default_account, password="test"
    )


@pytest.mark.asyncio
async def test_upgrade_account(bitshares, default_account, unused_account):
    account = await unused_account()
    await bitshares.create_account(
        account, referrer=default_account, registrar=default_account, password="test"
    )
    await bitshares.transfer(
        account, 10000, "TEST", memo="xxx", account=default_account
    )
    await bitshares.upgrade_account(account=account)


@pytest.mark.asyncio
async def test_allow_disallow(bitshares, default_account):
    await bitshares.allow("init1", account=default_account)
    await asyncio.sleep(1.1)
    await bitshares.disallow("init1", account=default_account)


@pytest.mark.asyncio
async def test_update_memo_key(bitshares, default_account):
    from bitsharesbase.account import PasswordKey

    password = "test"
    memo_key = PasswordKey(default_account, password, role="memo")
    pubkey = memo_key.get_public_key()
    await bitshares.update_memo_key(pubkey, account=default_account)


@pytest.mark.asyncio
async def test_approve_disapprove_witness(bitshares, default_account):
    witnesses = ["init1", "init2"]
    await bitshares.approvewitness(witnesses, account=default_account)
    await asyncio.sleep(1.1)
    await bitshares.disapprovewitness(witnesses, account=default_account)


@pytest.mark.asyncio
async def test_approve_disapprove_committee(bitshares, default_account):
    cm = ["init5", "init6"]
    await bitshares.approvecommittee(cm, account=default_account)
    await asyncio.sleep(1.1)
    await bitshares.disapprovecommittee(cm, account=default_account)


@pytest.mark.asyncio
async def test_approve_proposal(bitshares, default_account):
    parent = bitshares.new_tx()
    proposal = bitshares.new_proposal(parent=parent)
    await bitshares.transfer(
        "init1", 1, "TEST", append_to=proposal, account=default_account
    )
    await proposal.broadcast()
    proposals = await Proposals(default_account)
    assert len(proposals) == 1
    await bitshares.approveproposal(proposals[0]["id"], account=default_account)


@pytest.mark.asyncio
async def test_disapprove_proposal(bitshares, default_account, unused_account):
    # Create child account
    account = await unused_account()
    await bitshares.create_account(
        account, referrer=default_account, registrar=default_account, password="test"
    )
    await bitshares.transfer(account, 100, "TEST", account=default_account)

    # Grant child account access with 1/2 threshold
    await bitshares.allow(account, weight=1, threshold=2, account=default_account)

    # Create proposal
    parent = bitshares.new_tx()
    proposal = bitshares.new_proposal(parent=parent)
    await bitshares.transfer(
        "init1", 1, "TEST", append_to=proposal, account=default_account
    )
    await proposal.broadcast()
    proposals = await Proposals(default_account)
    assert len(proposals) == 1

    # Approve proposal; 1/2 is not sufficient to completely approve, so proposal remains active
    await bitshares.approveproposal(proposals[0]["id"], account=account)
    # Revoke vote
    await bitshares.disapproveproposal(proposals[0]["id"], account=account)


@pytest.mark.asyncio
async def test_approve_disapprove_worker(bitshares, testworker, default_account):
    workers = await Workers(default_account)
    worker = workers[0]["id"]
    await bitshares.approveworker(worker)
    await bitshares.disapproveworker(worker)


@pytest.mark.asyncio
async def test_set_unset_proxy(bitshares, default_account):
    await bitshares.set_proxy("init1", account=default_account)
    await bitshares.unset_proxy()


@pytest.mark.skip(reason="cancel() tested indirectly in test_market.py")
@pytest.mark.asyncio
async def test_cancel():
    pass


@pytest.mark.skip(reason="need to provide a way to make non-empty vesting balance")
@pytest.mark.asyncio
async def test_vesting_balance_withdraw(bitshares, default_account):
    balances = await bitshares.rpc.get_vesting_balances(default_account)
    await bitshares.vesting_balance_withdraw(balances[0]["id"], account=default_account)


@pytest.mark.asyncio
async def test_publish_price_feed(bitshares, default_account, bitasset):
    price = await Price("1.0 CNY/TEST")
    await bitshares.publish_price_feed("CNY", price, account=default_account)


@pytest.mark.asyncio
async def test_update_cer(bitshares, default_account, bitasset):
    price = await Price("1.2 CNY/TEST")
    await bitshares.update_cer("CNY", price, account=default_account)


@pytest.mark.asyncio
async def test_update_witness(bitshares, default_account):
    pass


@pytest.mark.asyncio
async def test_reserve(bitshares, default_account):
    pass


@pytest.mark.asyncio
async def test_create_asset(bitshares, default_account, bitasset):
    asset = await Asset("CNY")
    assert asset.is_bitasset


@pytest.mark.asyncio
async def test_create_worker(testworker, default_account):
    w = await Workers(default_account)
    assert len(w) > 0


@pytest.mark.asyncio
async def test_fund_fee_pool(bitshares, default_account):
    pass


@pytest.mark.asyncio
async def test_create_committee_member(bitshares, default_account):
    pass


@pytest.mark.asyncio
async def test_account_whitelist(bitshares, default_account):
    pass


@pytest.mark.asyncio
async def test_bid_collateral(bitshares, default_account):
    pass


@pytest.mark.asyncio
async def test_asset_settle(bitshares, default_account):
    pass


@pytest.mark.asyncio
async def test_htlc_create(bitshares, default_account):
    pass


@pytest.mark.asyncio
async def test_htlc_redeem(bitshares, default_account):
    pass
