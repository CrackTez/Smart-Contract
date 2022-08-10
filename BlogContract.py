import smartpy as sp

class PostLedger:
    def get_type():
        return sp.TRecord(
                author = sp.TAddress,
                title = sp.TString,
                thumbnail_url = sp.TString,
                ipfs_url = sp.TString,
                timestamp = sp.TTimestamp,
                fundraising_goal = sp.TMutez,
                fundraised = sp.TMutez,
                contributers = sp.TMap(sp.TAddress, sp.TMutez)
            )

class Contract(sp.Contract):
    def __init__(self):
        # Storage
        self.init_storage(
            admin = sp.address("tz1VLj6WqWLeFjn4BWdoScpN752qSEyqwXFV"),
            posts = sp.big_map(l = {}, tkey = sp.TNat, tvalue = PostLedger.get_type()),
            next_count = sp.nat(0)
        )

    #@sp.entry_point
    #def set_storage_from(self, addr):
    #    sp.set_type(addr, sp.TAddress)
    #    sp.verify(sp.sender == self.data.admin, "UNAUTHORISED")
    #    NextCount = sp.view("GetNextCount", addr, sp.nat(0), t=sp.TNat)
    #    Posts = sp.view("GetPosts", addr, sp.nat(0), t=sp.TBigMap(sp.TNat,PostLedger.get_type()))
    #    self.data.next_count = NextCount.open_some()
    #    self.data.posts = Posts.open_some()

    @sp.entry_point
    def create_post(self, ipfs_url, thumbnail_url, title, fr_goal):
        sp.set_type(ipfs_url, sp.TString)
        sp.set_type(title, sp.TString)
        sp.set_type(thumbnail_url, sp.TString)
        sp.set_type(fr_goal, sp.TMutez)
 
        self.data.posts[self.data.next_count] = sp.record(
            author = sp.sender,
            ipfs_url = ipfs_url,
            thumbnail_url = thumbnail_url,
            title = title,
            timestamp = sp.now,
            fundraising_goal = fr_goal,
            fundraised = sp.mutez(0),
            contributers = sp.map(l={}, tkey=sp.TAddress, tvalue = sp.TMutez)
        )
        self.data.next_count += 1

    @sp.entry_point
    def send_tip(self, post_id):
        sp.set_type(post_id, sp.TNat)

        sp.verify(self.data.posts.contains(post_id), "POST DOES NOT EXIST")
        post = self.data.posts[post_id]
        sp.verify(sp.sender != post.author, "AUTHOR CANNOT TIP OWN POSTS")

        contributers = post.contributers

        contribute_amt = sp.local("contribute_amt", sp.amount)
        sp.send(post.author,contribute_amt.value)
        post.fundraised += contribute_amt.value
        sp.if contributers.contains(sp.sender):
            contribute_amt.value += contributers[sp.sender]
        contributers[sp.sender] = contribute_amt.value

    #@sp.onchain_view(name = "GetNextCount")
    #def get_next_count(self, x):
    #    sp.set_type(x, sp.TNat)
    #    sp.result(self.data.next_count)

    #@sp.onchain_view(name = "GetPosts")
    #def get_posts(self, x):
    #    sp.set_type(x, sp.TNat)
    #    sp.result(self.data.posts)

        

@sp.add_test(name="main")
def main():
    scenario = sp.test_scenario()
    
    cont = Contract()
    scenario += cont

    weeblet = sp.address("tz1VLj6WqWLeFjn4BWdoScpN752qSEyqwXFV")
    other = sp.test_account ("oth")
    other1 = sp.test_account ("oth1")

    cont.create_post(
        ipfs_url="ok",
        thumbnail_url="ok",
        title="Demo Post, ghgh",
        fr_goal = sp.tez(69)
    ).run(sender = weeblet)

    cont.send_tip(0).run(sender=other1, amount=sp.mutez(10000))
    cont.send_tip(0).run(sender=other, amount=sp.tez(1))
    cont.send_tip(0).run(sender=weeblet, amount=sp.tez(2), valid=False)
    cont.send_tip(0).run(sender=other, amount=sp.tez(2))

    #v = sp.view("GetNextCount", cont.address, sp.nat(0), t=sp.TNat)
    #scenario.show(v)
    #v = sp.view("GetPosts", cont.address, sp.nat(0), t=sp.TBigMap(sp.TNat,PostLedger.get_type()))
    #scenario.show(v)

    #c2 = Contract()
    #scenario += c2

    #c2.set_storage_from(cont.address).run(sender=weeblet)
    #c2.set_storage_from(cont.address).run(sender=other, valid=False)
