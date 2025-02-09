import os
os.environ['DATABASE_URL'] = 'sqlite://'

import unittest
from datetime import datetime, timezone, timedelta
from app import app, db
from app.models import User, Post


class UserModelClass(unittest.TestCase):
    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        u = User(username='susan', email='susan@example.com')
        u.set_password('cat')
        self.assertFalse(u.check_password('dog'))
        self.assertTrue(u.check_password('cat'))

    def test_avatar(self):
        u = User(username='john', email='john@example.com')
        self.assertEqual(u.avatar(128), 'https://gravatar.com/avatar/'
                                        'd4c74594d841139328695756648b6bd6'
                                        '?d=identicon&s=128')
        
    def test_follow(self):
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='susan', email='susan@example.com')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        following = db.session.scalars(u1.following.select()).all()
        followers = db.session.scalars(u2.followers.select()).all()
        self.assertEqual(following, [])
        self.assertEqual(followers, [])

        u1.follow(u2)
        db.session.commit()
        self.assertTrue(u1.is_following(u2))
        self.assertEqual(u1.following_count(), 1)
        self.assertEqual(u2.followers_count(), 1)
        u1_following = db.session.scalars(u1.following.select()).all()
        u2_followers = db.session.scalars(u2.followers.select()).all()
        self.assertEqual(u1_following[0].username, 'susan')
        self.assertEqual(u2_followers[0].username, 'john')

        u1.unfollow(u2)
        db.session.commit()
        self.assertFalse(u1.is_following(u2))
        self.assertEqual(u1.following_count(), 0)
        self.assertEqual(u2.followers_count(), 0)

    def test_follow_post(self):
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='susan', email='susan@example.com')
        u3 = User(username='mary', email='mary@example.com')
        u4 = User(username='david', email='david@example.com')
        db.session.add_all([u1, u2, u3, u4])

        now = datetime.now(timezone.utc)
        post1 = Post(body='post from john', author=u1, timestamp=now + timedelta(seconds=1))
        post2 = Post(body='post from susan', author=u2, timestamp=now + timedelta(seconds=2))
        post3 = Post(body='post from mary', author=u3, timestamp=now + timedelta(seconds=3))
        post4 = Post(body='post from david', author=u4, timestamp=now + timedelta(seconds=4))
        db.session.add_all([post1, post2, post3, post4])
        db.session.commit()

        u1.follow(u2)
        u1.follow(u4)
        u2.follow(u3)
        u3.follow(u4)
        db.session.commit()

        follow1 = db.session.scalars(u1.following_posts()).all()
        follow2 = db.session.scalars(u2.following_posts()).all()
        follow3 = db.session.scalars(u3.following_posts()).all()
        follow4 = db.session.scalars(u4.following_posts()).all()
        self.assertEqual(follow1, [post4, post2, post1])
        self.assertEqual(follow2, [post3, post2])
        self.assertEqual(follow3, [post4, post3])
        self.assertEqual(follow4, [post4])
        

if __name__ == '__main__':
    unittest.main(verbosity=2)