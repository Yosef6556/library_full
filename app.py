import json
from xmlrpc.client import Boolean
from flask import Flask, request, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, String, Integer, ForeignKey, Date, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, date
from flask_cors import CORS


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.sqlite3'
app.config['SECRET_KEY'] = "random string"

db = SQLAlchemy(app)
CORS(app)


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)


app.json_encoder = CustomJSONEncoder


class Customer(db.Model):
    __tablename__ = 'customers'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    city = Column(String)
    age = Column(Integer)

    def __repr__(self):
        return f"<Customer_id={self.id}, name='{self.name}', city='{self.city}', age={self.age})>"

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'city': self.city,
            'age': self.age,
        }


@app.route('/')
def hello():
    return render_template('index.html')


@app.route("/customers")
def cust_show():
    cust_list = [customer.to_dict() for customer in Customer.query.all()]
    json_data = json.dumps(cust_list)
    return json_data


@app.route("/customers/update/<int:id>", methods=['PUT'])
def cust_update(id):
    customer = Customer.query.get(id)
    if customer:
        data = request.get_json()
        customer.name = data.get('name', customer.name)
        customer.city = data.get('city', customer.city)
        customer.age = data.get('age', customer.age)
        db.session.commit()
        return jsonify({'message': 'Customer updated successfully'})
    return jsonify({'message': 'Customer not found'})



@app.route('/customers/search/<string:name>', methods=['GET'])
def search_customer(name):
    customers = Customer.query.filter(Customer.name.ilike(f'%{name}%')).all()
    if not customers:
        return {'message': 'No customers found.'}, 404

    customer_list = [customer.to_dict() for customer in customers]
    return json.dumps(customer_list)




@app.route('/customers/new', methods=['POST'])
def newcust():
    data = request.get_json()
    name = data['name']
    city = data['city']
    age = data['age']

    new_customer = Customer(name=name, city=city, age=age)
    db.session.add(new_customer)
    db.session.commit()
    return "A new Library Customer was created."


@app.route('/customers/delete/<int:id>', methods=['DELETE'])
def delete_customer(id):
    customer = Customer.query.get_or_404(id)

    db.session.delete(customer)
    db.session.commit()

    return {"message": "Customer deleted successfully."}





class Book(db.Model):
    __tablename__ = 'books'
    id = Column(Integer, primary_key=True)
    bookname = Column(String)
    writer = Column(String)
    year_published = Column(Integer)
    book_loan = Column(Integer)
    loan_active = Column(Integer, default=0)
    
    __table_args__ = (
        CheckConstraint(loan_active.in_([0, 1]), name='check_loan_active'),
    )

    def __repr__(self):
        return f"<Book(id={self.id}, name='{self.bookname}', author='{self.writer}', year_published={self.year_published}, type={self.book_loan})>"

    def to_dict(self):
        return {
            'id': self.id,
            'bookname': self.bookname,
            'writer': self.writer,
            'year_published': self.year_published,
            'book_loan': self.book_loan,
            'loan_active': bool(self.loan_active),  # Convert to boolean for JSON serialization
        }

        

#book start
@app.route("/books")
def book_show():
    book_list = [book.to_dict() for book in Book.query.all()]
    json_data = json.dumps(book_list)
    return json_data


@app.route("/books/update/<int:id>", methods=['PUT'])
def book_update(id):
    book = Book.query.get(id)
    if book:
        data = request.get_json()
        book.bookname = data.get('bookname', book.bookname)
        book.writer = data.get('writer', book.writer)
        book.year_published = data.get('year_published', book.year_published)
        book.book_loan = data.get('book_loan', book.book_loan)
        db.session.commit()
        return jsonify({'message': 'Book updated successfully'})
    return jsonify({'message': 'Book not found'})



@app.route('/books/new', methods=['POST'])
def newbook():
    data = request.get_json()
    bookname = data['bookname']
    writer = data['writer']
    year_published = data['year_published']
    book_loan = data['book_loan']

    new_book = Book(bookname=bookname, writer=writer, year_published=year_published, book_loan=book_loan)
    db.session.add(new_book)
    db.session.commit()
    return "A new book record was created."


@app.route('/books/delete/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    return {"message": "Book deleted successfully."}


@app.route('/books/search/<string:name>', methods=['GET'])
def search_books(name):
    books = Book.query.filter(Book.bookname.ilike(f'%{name}%')).all()
    if not books:
        return {'message': 'No book found.'}, 404

    book_list = [book.to_dict() for book in books]
    return json.dumps(book_list)



class Loan(db.Model):
    __tablename__ = 'loans'
    id = Column(Integer, primary_key=True)
    cust_id = Column(Integer, ForeignKey('customers.id'))
    book_id = Column(Integer, ForeignKey('books.id'))
    loan_date = Column(Date)
    return_date = Column(Date)

    customer = relationship("Customer", backref="loans")
    book = relationship("Book", backref="loans")

    def __repr__(self):
        return f"<Loan(cust_id={self.cust_id}, book_id={self.book_id}, loan_date='{self.loan_date}', return_date='{self.return_date}')>"

    def to_dict(self):
        return {
            'cust_id': self.cust_id,
            'book_id': self.book_id,
            'loan_date': self.loan_date,
            'return_date': self.return_date,
        }




@app.route("/loans")
def loan_show():
    loan_list = []
    loans = db.session.query(Loan, Customer, Book).join(Customer).join(Book).all()

    for loan, customer, book in loans:
        loan_data = loan.to_dict()
        loan_data['customer_name'] = customer.name
        loan_data['book_name'] = book.bookname
        loan_list.append(loan_data)

    json_data = json.dumps(loan_list, default=str)
    return json_data

# CREATE A HTML TO DISPLAY LATE LOANS
@app.route("/late_loans")
def late_loan_show():
    loan_list = []
    loans = db.session.query(Loan, Customer, Book).join(Customer).join(Book).all()

    for loan, customer, book in loans:
        loan_data = loan.to_dict()
        loan_data['customer_name'] = customer.name
        loan_data['book_name'] = book.bookname
        if check_return_date(loan.return_date):
            loan_list.append(loan_data)

    json_data = json.dumps(loan_list, default=str)
    return json_data


def check_return_date(return_date):
    current_date = datetime.now()
    if current_date > datetime(return_date.year, return_date.month, return_date.day):
       return True
    return False



@app.route('/loans/new', methods=['POST'])
def new_loan():
    data = request.get_json()
    
    cust_name = data['cust_name']
    book_name = data['book_name']
    loan_date = datetime.strptime(data['loan_date'], '%Y-%m-%d').date()
    return_date = datetime.strptime(data['return_date'], '%Y-%m-%d').date()

    customer = Customer.query.filter_by(name=cust_name).first()
    book = Book.query.filter_by(bookname=book_name).first()

    if not customer:
        return {"error": f"Customer '{cust_name}' not found."}, 404

    if not book:
        return {"error": f"Book '{book_name}' not found."}, 404

    if book.loan_active == 1:
        return {"error": "Book is already on loan."}, 400

    new_loan = Loan(cust_id=customer.id, book_id=book.id, loan_date=loan_date, return_date=return_date)
    db.session.add(new_loan)
    book.loan_active = 1  # Update the loan_active status of the book
    db.session.commit()
    return "A new loan record was created."



@app.route('/returnbook', methods=['POST'])
def return_book():
    data = request.get_json()
    cust_name = data['cust_name']
    book_name = data['book_name']

    loan = Loan.query.join(Customer).join(Book).filter(Customer.name == cust_name, Book.bookname == book_name).first()

    if not loan:
        return "No loan record found for the given customer and book."

    if not loan.book.loan_active:
        return "Book is already marked as returned."

    loan.book.loan_active = False
    loan.return_date = date.today()
    db.session.commit()

    return "Book returned successfully."



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
