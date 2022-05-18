import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows, Likes

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

db.create_all()

class MessageModelTestCase(TestCase):
    """Test message model"""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

        self.u = User(
            email="test@test.com",
            username="testuser",
            password="123"
        )
        db.session.add(self.u)
        db.session.commit()


    def tearDown(self):
        """Remove sample data after each test."""
        
        db.session.rollback()


    def test_message_model(self):
        """Does the basic model work?"""

        m = Message(
            text="This is a test message.",
            user_id=self.u.id
        )
        db.session.add(m)
        db.session.commit()

        
        self.assertIsInstance(m, Message)
        self.assertEqual(len(self.u.messages), 1)
        self.assertEqual(self.u.messages[0].text, "This is a test message.")

    
    def test_message_likes(self):

        m = Message(
            id=5,
            text="This is a test message.",
            user_id=self.u.id
        )
        db.session.add(m)

        l = Likes(
            user_id=self.u.id,
            message_id=5
        )
        db.session.add(l)
        db.session.commit()

        self.assertEqual(l.user_id, self.u.id)
        self.assertEqual(l.message_id, 5)
        self.assertEqual(len(m.user.likes), 1)

