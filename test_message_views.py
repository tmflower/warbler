"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()

    def tearDown(self):
        db.session.rollback()

    def test_add_message(self):
        """Can user add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_add_message_not_logged_in(self):
        """Is unauthorized user prevented from adding messages?"""

        with self.client as c:        
            
            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))


    def test_show_message(self):
        """Does individual message display when selected?"""

        m = Message(
            id=3,
            text="I am a test message.",
            user_id=self.testuser.id
        )
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY]= self.testuser.id

            m = Message.query.get(3)
            resp = c.get(f"/messages/{m.id}")
            html = resp.get_data(as_text=True)

            self.assertIn("I am a test message.", html)
            self.assertIn('<ul class="list-group no-hover" id="messages">', html)


    def test_delete_message(self):
        """Can user delete their own messages?"""

        m = Message(
            id=3,
            text="Delete me.",
            user_id=self.testuser.id
            )

        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY]= self.testuser.id

            resp = c.post('/messages/3/delete', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            mess = Message.query.get(3)
            self.assertIsNone(mess)


    def test_prevent_delete_message(self):
        """Is user prevented from deleting messages that are not their own?"""

        u2 = User(
            username="testuser2",
            email="test2@test.com",
            password="testuser2",
            image_url=None
            )
        u2.id = 7

        m2 = Message(
            id=4,
            text="I am a test message.",
            user_id=self.testuser.id
            )

        db.session.add_all([u2, m2])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY]= 7

            resp = c.post('/messages/4/delete', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIsNotNone(m2)


    def test_delete_message_not_logged_in(self):
        """Is unauthorized user prevented from deleting messages?"""
        
        m = Message(
            id=7,
            text="Try to delete me",
            user_id=self.testuser.id
        )
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            resp = c.post("/messages/7/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            m = Message.query.get(7)
            self.assertIsNotNone(m)