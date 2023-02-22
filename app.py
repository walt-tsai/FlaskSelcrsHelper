import base64
import sys

from flask import Flask, render_template, request, redirect, flash, url_for
from http import cookiejar
import mechanize
import io
from bs4 import BeautifulSoup
from PIL import Image

app = Flask(__name__)
app.secret_key = '0ee4897d35f922a0aa5bb9fc30866f90'

url = 'https://selcrs.nsysu.edu.tw/'

br: mechanize.Browser
cj: cookiejar.CookieJar


@app.route('/', methods=('GET', 'POST'))
def redirect_to_login():
    return redirect(url_for('login'), code=307)


#h-100 d-flex align-items-top justify-content-left
@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        global br
        br.select_form(nr=0)
        br.form['stuid'] = request.form['stuid']
        br.form['SPassword'] = request.form['SPassword']
        br.form['ValidCode'] = request.form['ValidCode']
        br.submit()
        if 'Wrong ID or password' in str(br.response().read()):
            flash('輸入帳號或密碼錯誤!', category='error')
        elif 'Wrong Validation Code' in str(br.response().read()):
            flash('輸入驗證碼錯誤!', category='error')
        elif 'Course Selection System' in str(br.response().read()):
            return redirect(url_for('course_page'), code=307)
        return render_template('log_in.html', verification=encode_image().decode('utf-8'), stuid=request.form['stuid'], pwd=request.form['SPassword'])
    return render_template('log_in.html', verification=encode_image().decode('utf-8'))


@app.route('/courses', methods=('GET', 'POST'))
def course_page():
    global br
    response = br.open('https://selcrs.nsysu.edu.tw/menu4/query/slt_result.asp?admit=0')
    soup = BeautifulSoup(response.read().decode('big5'), 'html.parser')
    table = soup.find_all('table')[0].find_all_next('tr')
    del table[0]

    courses = list()
    for element in table:
        data = element.find_next('a').attrs['href']
        data = data[data.index('?')+1:]
        selected = 1 if '選上' in str(element) else -1 if '失敗' in str(element) else 0

        course = {'selected': selected,
                  'year': data[data.index('syear='):data.find('&', data.index('syear='))].replace('syear=', ''),
                  'sem': data[data.index('sem='):data.find('&', data.index('sem='))].replace('sem=', ''),
                  'code': data[data.index('CrsDat='):data.find('&', data.index('CrsDat='))].replace('CrsDat=', ''),
                  'name': data[data.index('Crsname='):].replace('Crsname=', '')
                  }
        courses.append(course)
        #'https://selcrs.nsysu.edu.tw/menu5/showoutline.asp?SYEAR=111&SEM=2&CrsDat=CSE103'

    return render_template('courses.html', course_response=courses)


def encode_image():
    im = Image.open(io.BytesIO(web_scrap()))
    data = io.BytesIO()
    im.save(data, "JPEG")
    return base64.b64encode(data.getvalue())

def web_scrap():
    global br, cj
    br = mechanize.Browser()
    cj = cookiejar.CookieJar()
    br.set_cookiejar(cj)

    response = br.open(url)
    soup = BeautifulSoup(response.get_data(), 'html.parser')
    img = soup.find('img', id='imgVC')
    image_response = br.open_novisit(img['src'])
    return image_response.get_data()


if __name__ == '__main__':
    app.run()
