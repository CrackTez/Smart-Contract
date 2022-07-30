import smartpy as sp

class PostLedger: 
    # Providing type to Values
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
        # Storing Default Values
        self.init(
            posts = sp.big_map(l = {}, tkey = sp.TNat, tvalue = PostLedger.get_type()),
            next_count = sp.nat(0)
        )

    @sp.entry_point
    def create_post(self, ipfs_url, thumbnail_url, title, fr_goal):
        # Type Constraining
        sp.set_type(ipfs_url, sp.TString)
        sp.set_type(title, sp.TString)
        sp.set_type(thumbnail_url, sp.TString)
        sp.set_type(fr_goal, sp.TMutez)
 
        # Storage Updates
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

        # Verification statements
        sp.verify(self.data.posts.contains(post_id), "POST DOES NOT EXIST")
        post = self.data.posts[post_id]
        sp.verify(sp.sender != post.author, "AUTHOR CANNOT TIP OWN POSTS")

        contributers = post.contributers

        contribute_amt = sp.local("contribute_amt", sp.amount)
        sp.if contributers.contains(sp.sender):
            contribute_amt.value += contributers[sp.sender]
        sp.send(post.author,sp.amount)
        post.fundraised += sp.amount
        contributers[sp.sender] = contribute_amt.value

        

@sp.add_test(name="main")
def main():
    scenario = sp.test_scenario()
    
    # Create Contract
    cont = Contract()
    scenario += cont

    # Test address
    weeblet = sp.test_account ("weeblet")
    other = sp.test_account ("oth")
    other1 = sp.test_account ("oth1")

    cont.create_post(
        ipfs_url="ok",
        thumbnail_url="ok",
        title="Demo Post",
        fr_goal = sp.tez(69)
    ).run(sender = weeblet)

    # Change Create Post
    cont.send_tip(0).run(sender=other1.address, amount=sp.mutez(10000))
    cont.send_tip(0).run(sender=other.address, amount=sp.tez(1))
    cont.send_tip(0).run(valid=False, sender=weeblet.address, amount=sp.tez(2))
    cont.send_tip(0).run(sender=other.address, amount=sp.tez(2))

