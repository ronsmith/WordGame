from flask import Flask, render_template

app = Flask('WordGame')
app.config['SECRET_KEY'] = 't(X9Day:V{nygE8+3Q36(9h#<)u7=i]U,X/?Xrd`)pt+BHR&x+d/HX9<k.l=rbS'


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run()
