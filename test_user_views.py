import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes, Follows

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False

class UserViewTestCase(TestCase):
    """Test views for user"""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Likes.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        self.u2 = User.signup(username="seconduser",
                        email="test2@test.com",
                        password="123456",
                        image_url=None
                        )

        self.u3 = User.signup(username="thirduser",
                email="test3@test.com",
                password="abcde",
                image_url=None
                )

        db.session.commit()


    def tearDown(self):
        db.session.rollback()


    def test_users_list(self):
        """Does list of users appear?"""
        
        with self.client as c:
            resp = c.get('/users')

        self.assertEqual(resp.status_code, 200)
        self.assertIn(f'<a href="/users/{ self.testuser.id }" class="card-link">', str(resp.data))
        self.assertIn("@testuser", str(resp.data))


    def test_user_search(self):
        """Does user search query return matching users?"""

        with self.client as c:
            resp = c.get('/users?q=test')

        self.assertEqual(resp.status_code, 200)
        self.assertIn("testuser", str(resp.data))
        self.assertNotIn("fakeuser", str(resp.data))


    def test_user_profile(self):
        """Does profile show user details?"""

        with self.client as c:
            resp = c.get(f"/users/{self.testuser.id}")

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<ul class="list-group" id="messages">', str(resp.data))


    def setup_likes(self):
        """Generate messages and likes to use in testing user likes view"""
        
        m1 = Message(text="Hello!", user_id=self.testuser.id)
        m2 = Message(text="Goodbye!", user_id=self.u2.id)
        m3 = Message(text="You say goodbye and I say hello.", user_id=self.testuser.id)

        l1 = Likes(user_id=self.testuser.id, message_id=m2.id)
        l2 = Likes(user_id=self.u2.id, message_id=m3.id)

        db.session.add_all([m1, m2, m3, l1, l2])
        db.session.commit()


    def test_show_likes(self):
        """Do user's liked messages show?"""

        self.setup_likes()
        with self.client as c:
            resp = c.get(f"/users/{self.testuser.id}")

            self.assertEqual(resp.status_code, 200)
            self.assertIn("You say goodbye and I say hello.", str(resp.data))
            self.assertIn("Hello!", str(resp.data))
            self.assertNotIn("Goodbye!", str(resp.data))

    def test_add_like(self):
        """Can user add a like to message?"""

        m4 = Message(id=7, text="This is the end.", user_id=self.u2.id)
        db.session.add(m4)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
               
            resp = c.post('/users/add_like/7', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.user_id==self.testuser.id).all()
            self.assertEqual(len(likes), 1)


    def test_remove_like(self):
        """Can a user remove a like from a message?"""
        
        m4 = Message(id=7, text="This is the end.", user_id=self.u2.id)
        db.session.add(m4)
        db.session.commit()        

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            """Adding the like first, as tested above"""
            c.post('/users/add_like/7', follow_redirects=True)
            
            """Then removing the like using the same view function"""
            resp = c.post('/users/add_like/7', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            
            likes = Likes.query.filter(Likes.user_id==self.testuser.id).all()
            self.assertEqual(len(likes), 0)


    def test_unauthenticated_like(self):
        """Can a user who is not logged in add a like?"""

        m4 = Message(id=7, text="This is the end.", user_id=self.u2.id)
        db.session.add(m4)
        db.session.commit()        

        with self.client as c:
            resp = c.post('/users/add_like/7', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", str(resp.data))
            
    def setup_follows(self):

        f1 = Follows(user_being_followed_id = self.u3.id, user_following_id = self.testuser.id)   
        f2 = Follows(user_being_followed_id = self.u2.id, user_following_id = self.testuser.id)   
        f3 = Follows(user_being_followed_id = self.testuser.id, user_following_id = self.u2.id)   

        db.session.add_all([f1, f2, f3])
        db.session.commit()

    def test_user_is_following(self):
        """Do those who the user is following display accurately?"""
        
        self.setup_follows()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            resp = c.get(f'/users/{self.testuser.id}/following')
            self.assertEqual(resp.status_code, 200)

            following = Follows.query.filter(Follows.user_following_id == self.testuser.id).all()
            self.assertEqual(len(following), 2)
            self.assertIn('@seconduser', str(resp.data))


    def test_user_being_followed_by(self):
        """Do the user's followers display accurately?"""

        self.setup_follows()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            resp = c.get(f'/users/{self.testuser.id}/followers')
            self.assertEqual(resp.status_code, 200)

            followers = Follows.query.filter(Follows.user_being_followed_id == self.testuser.id).all()
            self.assertEqual(len(followers), 1)
            self.assertIn('@seconduser', str(resp.data))
            self.assertNotIn('@thirduser', str(resp.data))
            

    def test_unauthorized_access_to_followers(self):
        """Can unauthorized user view list of a user's followers?"""

        with self.client as c:
            resp = c.get(f'/users/{self.testuser.id}/followers', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", str(resp.data))


    def test_unauthorized_access_to_following(self):
        """Can unauthorized user view list of those who a user is following?"""

        with self.client as c:
            resp = c.get(f'/users/{self.testuser.id}/following', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", str(resp.data))