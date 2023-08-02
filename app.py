from flask import Flask, abort, request
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import os 
from dotenv import load_dotenv

load_dotenv()
database_url = os.getenv("DATABASE_URL")

app = Flask(__name__)

def protected(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization')
        
        if not auth:
            return {"error": "No authorization header provided."}, 401
        
        username = request.authorization.username
        password = request.authorization.password
        
        if username != "admin" or password != "admin@123":
            return {"error": "Invalid credentials."}, 401
       
        return f(*args, **kwargs)
    return decorated

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    level = db.Column(db.String(100), nullable=False)
    
    def __repr__(self):
        return f"Member(name={self.name}, level={self.level})"

with app.app_context():
    db.create_all()
    

@app.route("/member", methods=["GET"])
@protected
def get_members():
    members = Member.query.all()
    if not members:
        abort(404, "Member not found.")
        
    sorted_members = sorted(members, key=lambda member: member.id)
    
    results = [
        {
            "id": member.id,
            "name": member.name,
            "email": member.email,
            "level": member.level
        } for member in sorted_members]
    

    return {"members": results}

@app.route("/member", methods=["POST"])
@protected
def add_member():
    new_member_data = request.get_json() 
    
    name = new_member_data['name']
    email = new_member_data['email']
    level = new_member_data['level']
    
    if not all([name, email, level]):
        return {"error": "Missing information."}
    
    if not isinstance(name, str) or not isinstance(email, str) or not isinstance(level, str):
        return {"error": "Invalid input type."}
    
    if "@" not in email or "." not in email:
        return {"error": "Invalid email."}

    member = Member.query.filter_by(email=email).first()
    if member:
        return {"error": "Email already exists."}
    
    new_member = Member(name=name, email=email, level=level)
    db.session.add(new_member)
    db.session.commit()
    
    get_member = {
        "id": new_member.id,
        "name": new_member.name,
        "email": new_member.email,
        "level": new_member.level
    }

    return {"member": get_member}

@app.route("/member/<int:member_id>", methods=["GET"])
@protected
def get_member(member_id):
    member = Member.query.filter_by(id=member_id).first()
    
    if not member:
        return {"error": "Invalid member ID."}

    member_data = {
        "id": member.id,
        "name": member.name,
        "email": member.email,
        "level": member.level
    }
    
    return {"member": member_data}

@app.route("/member/<int:member_id>", methods=["PUT", "PATCH"])
@protected
def update_member(member_id):
        member = Member.query.filter_by(id=member_id).first()
        
        if not member:
            return {"error": "Invalid member ID."}
        
        update_member_data = request.get_json()
        
        name = update_member_data['name']
        email = update_member_data['email']
        level = update_member_data['level']

        if not all([name, email, level]):
            return {"error": "Missing information."}
        
        if not isinstance(name, str) or not isinstance(email, str) or not isinstance(level, str):
            return {"error": "Invalid input type."}
        
        if "@" not in email or "." not in email:
            return {"error": "Invalid email."}
        
        member.name, member.email, member.level = name, email, level
        db.session.commit()
        db.session.refresh(member)
    
        member_data = {
            "id": member.id,
            "name": member.name,
            "email": member.email,
            "level": member.level
        }

        return {"member": member_data}
    
@app.route("/member/<int:member_id>", methods=["DELETE"])
@protected
def delete_member(member_id):
    member = Member.query.filter_by(id=member_id).first()
    
    if not member:
        return {"error": "Invalid member ID."}
    
    db.session.delete(member)
    db.session.commit()
    
    return {"message": "Member deleted."}


if __name__ == "__main__":
    app.run(debug=True)
