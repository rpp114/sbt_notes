from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String, index=True, unique=True)
    email = db.Column(db.String, index=True, unique=True)


    def __repr__(self):
        return '<User %r>' % (self.nickname)
