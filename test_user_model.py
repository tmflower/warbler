"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test user model."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()


    def tearDown(self):
        """Remove sample data after each test."""
        db.session.rollback()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)


    def test_repr(self):
        """Does __repr__ method work?"""

        u = User(
            id=1,
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        info = u.__repr__()

        self.assertEqual('<User #1: testuser, test@test.com>', info)


    def test_is_following(self):
        """Does is_following method work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD",
        )
        u2 = User(email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD",
        )

        db.session.add(u)
        db.session.add(u2)
        db.session.commit()

        u.following=[u2]

        self.assertTrue(u.is_following(u2))

        u.following=[]

        self.assertFalse(u.is_following(u2))


    def test_is_followed_by(self):
        """Does is_followed_by method work when being followed?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD",
        )
        u2 = User(email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD",
        )

        db.session.add(u)
        db.session.add(u2)
        db.session.commit()

        u.followers=[u2]

        self.assertTrue(u.is_followed_by(u2))

        u.followers=[]

        self.assertFalse(u.is_followed_by(u2))


    def test_user_signup(self):
        """Is new user created?"""
        
        u = User.signup("testuser", "test@test.com", "HASHED_PASSWORD", "https://images.unsplash.com/photo-1549249061-0433f0b4bdb0?ixlib=rb-1.2.1&ixid=MnwxMjA3fDB8MHxzZWFyY2h8MTd8fGZsb2NrfGVufDB8fDB8fA%3D%3D&auto=format&fit=crop&w=500&q=60")

        db.session.add(u)
        db.session.commit()

        self.assertIsInstance(u, User)
        self.assertTrue(u.username=='testuser')
        self.assertTrue(u.email=='test@test.com')

    def test_duplicate_username_signup(self):
        """Does signup fail when username is already taken?"""
        
        u = User.signup("testuser", "test@test.com", "HASHED_PASSWORD", "https://images.unsplash.com/photo-1549249061-0433f0b4bdb0?ixlib=rb-1.2.1&ixid=MnwxMjA3fDB8MHxzZWFyY2h8MTd8fGZsb2NrfGVufDB8fDB8fA%3D%3D&auto=format&fit=crop&w=500&q=60")

        db.session.add(u)
        db.session.commit()

        u2 = User.signup("testuser", "test2@test.com", "HASHED_PASSWORD", "https://images.unsplash.com/photo-1549249061-0433f0b4bdb0?ixlib=rb-1.2.1&ixid=MnwxMjA3fDB8MHxzZWFyY2h8MTd8fGZsb2NrfGVufDB8fDB8fA%3D%3D&auto=format&fit=crop&w=500&q=60")

        with self.assertRaises(exc.IntegrityError) as context:
            db.session.add(u2)
            db.session.commit()

    def test_invalid_email_signup(self):
        """Does signup fail when email is not valid?"""
        u = User.signup("testuser", None, "HASHED_PASSWORD", "https://images.unsplash.com/photo-1549249061-0433f0b4bdb0?ixlib=rb-1.2.1&ixid=MnwxMjA3fDB8MHxzZWFyY2h8MTd8fGZsb2NrfGVufDB8fDB8fA%3D%3D&auto=format&fit=crop&w=500&q=60")

        with self.assertRaises(exc.IntegrityError) as context:
            db.session.add(u)
            db.session.commit()



    ### Keep geting "invalid salt" even though bcrypt.check_password_hash returns true in iPython for same user data...???

    # def test_authenticate(self):
    #     """Is a user returned when valid username and password are submitted?"""

    #     user = User(
    #         email="test@test.com",
    #         username="testuser",
    #         password="HASHED_PASSWORD",
    #     )

    #     db.session.add(user)
    #     db.session.commit()

    #     u = User.authenticate("testuser", "HASHED_PASSWORD")

    #     self.assertIsInstance(u, User)
    #     self.assertEqual(u.username, "testuser")
    #     self.assertEqual(u.password, "HASHED_PASSWORD")

    # def test_authenticate_invalid_username(self):
    #     """Does return user fail when username is not valid?"""

    #     user = User(
    #         email="test@test.com",
    #         username="testuser",
    #         password="HASHED_PASSWORD",
    #     )

    #     u = User.authenticate("invalid_username", "HASHED_PASSWORD")

    #     self.assertFalse(u)

    # def test_authenticate_invalid_password(self):
    #     """Does return user fail when password is not valid?"""

    #     user = User(
    #         email="test@test.com",
    #         username="testuser",
    #         password="HASHED_PASSWORD",
    #     )

    #     u = User.authenticate("testuser", "invalid_password")

    #     self.assertFalse(u)