import smartpy as sp

class PostLedger: 
    def get_type():
        return sp.TRecord(
                author = sp.TAddress,
                copies_max = sp.TNat,
                copies_remaining = sp.TNat,
                title = sp.TString,
                thumbnail_url = sp.TString,
                ipfs_url = sp.TString,
                owners = sp.TMap(sp.TNat, sp.TRecord(owner_address=sp.TAddress, price=sp.TMutez, on_sale=sp.TBool)),
                royalty_percent = sp.TNat,
                timestamp = sp.TTimestamp
            )

class Contract(sp.Contract):
    def __init__(self):
        # Storage
        self.init(
            posts = sp.big_map(l = {}, tkey = sp.TNat, tvalue = PostLedger.get_type()),
            next_count = sp.nat(0)
        )

    @sp.entry_point
    def create_post(self, ipfs_url, price, copies, royalty, sell, thumbnail_url, title):
        sp.set_type(ipfs_url, sp.TString)
        sp.set_type(title, sp.TString)
        sp.set_type(thumbnail_url, sp.TString)
        sp.set_type(price, sp.TMutez)
        sp.set_type(copies, sp.TNat)
        sp.set_type(royalty, sp.TNat)
        sp.set_type(sell, sp.TBool)

        owners = sp.local("owners", sp.map(l={}, tkey=sp.TNat, tvalue=sp.TRecord(owner_address=sp.TAddress, price=sp.TMutez, on_sale=sp.TBool)))
        idx = sp.local("idx", sp.nat(1))
        sp.while idx.value <= copies:
            owners.value[idx.value] = sp.record(
                owner_address=sp.sender,
                price=price,
                on_sale=sell
            )
            idx.value += sp.nat(1)
 
        self.data.posts[self.data.next_count] = sp.record(
            author = sp.sender,
            copies_max = copies,
            copies_remaining = copies,
            ipfs_url = ipfs_url,
            thumbnail_url = thumbnail_url,
            title = title,
            owners = owners.value,
            royalty_percent = royalty,
            timestamp = sp.timestamp_from_utc_now()
        )
        self.data.next_count += 1

    @sp.entry_point
    def buy_post(self, post_id, copy_id):
        sp.set_type(post_id, sp.TNat)
        sp.set_type(copy_id, sp.TNat)

        sp.verify(self.data.posts.contains(post_id), "POST DOES NOT EXIST")
        post = self.data.posts[post_id]
        sp.verify(post.owners.contains(copy_id), "COPY DOES NOT EXIST")
        copy = post.owners[copy_id]
        
        sp.verify(sp.amount >= copy.price, "NOT ENOUGH TEZ")
        sp.verify(copy.on_sale, "NOT ON SALE")

        remaining_tez = sp.amount - copy.price
        author_share = sp.split_tokens(copy.price, post.royalty_percent, 100)
        reseller_share = copy.price - author_share
        sp.send(copy.owner_address, reseller_share)
        sp.send(post.author, author_share)
        sp.if remaining_tez > sp.tez(0):
            sp.send(sp.sender, remaining_tez)

        post.owners[copy_id] = sp.record(owner_address=sp.sender,price=copy.price,on_sale=sp.bool(False))

        sp.if post.copies_remaining > 0:
            post.copies_remaining = sp.as_nat(post.copies_remaining - 1)

    @sp.entry_point
    def set_sale(self, post_id, copy_id, sell, price):
        sp.set_type(post_id, sp.TNat)
        sp.set_type(copy_id, sp.TNat)
        sp.set_type(sell, sp.TBool)
        sp.set_type(price, sp.TMutez)

        sp.verify(self.data.posts.contains(post_id), "POST DOES NOT EXIST")
        post = self.data.posts[post_id]
        sp.verify(post.owners.contains(copy_id), "COPY DOES NOT EXIST")
        copy = post.owners[copy_id]

        sp.verify(copy.owner_address == sp.sender, "YOU DONT OWN THAT POST COPY")

        copy.on_sale = sell
        copy.price = price

    @sp.entry_point
    def transfer(self, post_id, copy_id, transfer_to):
        sp.set_type(post_id, sp.TNat)
        sp.set_type(copy_id, sp.TNat)
        sp.set_type(transfer_to, sp.TAddress)

        sp.verify(self.data.posts.contains(post_id), "POST DOES NOT EXIST")
        post = self.data.posts[post_id]
        sp.verify(post.owners.contains(copy_id), "COPY DOES NOT EXIST")
        copy = post.owners[copy_id]

        sp.verify(copy.owner_address == sp.sender, "UNAUTHORISED")

        post.owners[copy_id] = sp.record(owner_address=transfer_to, price=copy.price, on_sale=sp.bool(False))

@sp.add_test(name="main")
def main():
    scenario = sp.test_scenario()
    
    cont = Contract()
    scenario += cont

    weeblet = sp.test_account ("weeblet")
    other = sp.test_account ("oth")

    cont.create_post(
        ipfs_url="ok",
        thumbnail_url="ok",
        title="Demo Post",
        price = sp.tez(1),
        copies = sp.nat(10),
        royalty = sp.nat(10),
        sell = sp.bool(True)
    ).run(sender = weeblet)

    cont.buy_post(
        post_id=sp.nat(0),
        copy_id=sp.nat(1)
    ).run(sender=other, amount=sp.tez(1))

    cont.set_sale(
        post_id=sp.nat(0),
        copy_id=sp.nat(1),
        sell = sp.bool(True),
        price = sp.tez(1)
    ).run(sender=other)

    cont.buy_post(
        post_id=sp.nat(0),
        copy_id=sp.nat(1)
    ).run(sender=weeblet, amount=sp.tez(1))

    cont.transfer(
        post_id=sp.nat(0),
        copy_id=sp.nat(2),
        transfer_to = other.address
    ).run(sender=weeblet)
