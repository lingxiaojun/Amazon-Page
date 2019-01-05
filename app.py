import os

# Third party module import
from flask import Flask, render_template, redirect, url_for, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

INSTANCE_UPLOAD_FOLDER = '/media/uploads/'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///amazonpreview.db'
app.config['UPLOAD_FOLDER'] = os.path.dirname(app.instance_path) + INSTANCE_UPLOAD_FOLDER
db = SQLAlchemy(app)


class Amazon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    design_id = db.Column(db.String(80), nullable=True)
    product_image = db.Column(db.String(80), nullable=True)
    product_image_caption = db.Column(db.String(80), nullable=True)
    product_title = db.Column(db.String(80), nullable=True)
    product_subtitle = db.Column(db.String(80), nullable=True)
    product_content = db.Column(db.String(80), nullable=True)

    company_image = db.Column(db.String(80), nullable=True)
    campany_image_caption = db.Column(db.String(80), nullable=True)
    company_title = db.Column(db.String(80), nullable=True)
    company_content = db.Column(db.String(80), nullable=True)

    productdetails = db.relationship('ProductDetail', backref='amazon', lazy=True)
    productpoints = db.relationship('ProductPoint',  backref='amazon', lazy=True)
    companypoints = db.relationship('CompanyPoint',  backref='amazon', lazy=True)


class ProductDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    product_image = db.Column(db.String(80), nullable=True)
    product_image_caption = db.Column(db.String(80), nullable=True)
    product_title = db.Column(db.String(80), nullable=True)
    product_subtitle = db.Column(db.String(80), nullable=True)
    product_content = db.Column(db.String(80), nullable=True)

    amazon_id = db.Column(db.Integer, db.ForeignKey('amazon.id'))
    
class ProductPoint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(80), nullable=False)
    
    amazon_id = db.Column(db.Integer, db.ForeignKey('amazon.id'))


class CompanyPoint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(80), nullable=False)

    amazon_id = db.Column(db.Integer, db.ForeignKey('amazon.id')) 


# Write your view function
@app.route("/")
def index():
    amazons = Amazon.query.all()
    return render_template('index.html', amazons=amazons)


@app.route('/media/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


@app.route('/design')
@app.route('/design/')
@app.route('/design/<int:design_id>')
@app.route('/design/<int:design_id>/')
@app.route('/design/<int:design_id>/<int:amazon_id>')
@app.route('/design/<int:design_id>/<int:amazon_id>/')
def design(design_id=None, amazon_id=None):
    # If user doesn't enter domain redirect the user to default design page
    if not design_id:
        design_id = 1

    amazon = None
    if amazon_id:
        amazon = Amazon.query.get(amazon_id)
    
    return render_template('design/{}.html'.format(design_id), preview=True, design_id=design_id, amazon=amazon)


def allowed_file(filename):
    ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/submit", methods=['POST'])
def submit():
    design_id = request.form.get('design-id')
    amazon_id = request.form.get('amazon-id')
    if amazon_id:
        amazon = Amazon.query.get(amazon_id)
    else:
        amazon = Amazon()

    # The thing about design id is user can choose to update the design id -
    # whenever he wants for future changing the templates.
    amazon.design_id = design_id

    # Handle product image
    product_image = request.files.get('product-image')
    if product_image and allowed_file(product_image.filename):
        filename = secure_filename(product_image.filename)
        product_image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        amazon.product_image = INSTANCE_UPLOAD_FOLDER + filename

    amazon.product_image_caption = request.form.get('product-image-caption')
    amazon.product_title = request.form.get('product-title')
    amazon.product_subtitle = request.form.get('product-subtitle')
    amazon.product_content = request.form.get('product-content')

    company_image = request.files.get('company-image')
    if company_image and allowed_file(company_image.filename):
        filename = secure_filename(company_image.filename)
        company_image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        amazon.company_image = INSTANCE_UPLOAD_FOLDER + filename
    amazon.company_title = request.form.get('company-title')
    amazon.company_content = request.form.get('company-content')
    # company_bulletpoints = request.form.getlist('company-bulletpoint')

    db.session.add(amazon)
    db.session.commit()

    # Trying to implement separate product details model. This will be the -
    # Default integration for upcoming model so we need to make sure should be
    # backward compaitable.

    # After creating the product then this time to create the bulletpoint
    # We need to delete all the existing ones
    for key, value in enumerate(amazon.productpoints):
        db.session.delete(value)
        db.session.commit()

    product_bulletpoints = request.form.getlist('product-bulletpoints')
    for product_bulletpoint in product_bulletpoints:
        if product_bulletpoint:
            product_point = ProductPoint()
            product_point.text = product_bulletpoint
            product_point.amazon_id = amazon.id
            
            db.session.add(product_point)
            db.session.commit()


    for key, value in enumerate(amazon.companypoints):
        db.session.delete(value)
        db.session.commit()

    company_bulletpoints = request.form.getlist('company-bulletpoints')
    for company_bulletpoint in company_bulletpoints:
        if company_bulletpoint:
            company_point = CompanyPoint()
            company_point.text = company_bulletpoint
            company_point.amazon_id = amazon.id
            
            db.session.add(company_point)
            db.session.commit()

    return redirect(url_for("preview", amazon_id=amazon.id))


@app.route('/preview')
@app.route('/preview/')
@app.route("/preview/<int:amazon_id>")
def preview(amazon_id=None):
    # Sometimes user may navigate to preview page without design in this case
    # redirect the user to new page
    if not amazon_id:
        return redirect(url_for('design'))

    # Get amazon object for the preview
    amazon = Amazon.query.get(amazon_id)
    return render_template("preview/{}.html".format(amazon.design_id), design=True, amazon=amazon)
