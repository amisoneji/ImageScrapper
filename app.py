import os
import time
import zipfile
from typing import io

import requests
from selenium import webdriver
from flask_cors import CORS,cross_origin
from flask import Flask, render_template, request, jsonify, Response
import io

#app = Flask(__name__)
app = Flask(__name__, static_url_path='')

# initialising the flask app with the name 'app'
@app.route('/')  # route for redirecting to the home page
@cross_origin()
def home():
    return render_template('index.html')

@app.route('/searchImages', methods=['GET','POST']) # route to show the images on a webpage
@cross_origin()
def show_images():
    if request.method == "POST":
        try:
            search_term=request.form['content']
            print(search_term)
            print(type(search_term))
            number_images=int(request.form['Noofimages'])
            print(number_images)
            print(type(number_images))
            def fetch_image_urls(query: str, max_links_to_fetch: int, wd: webdriver, sleep_between_interactions: int = 1):
                def scroll_to_end(wd):
                    wd.execute_script("window.scrollTo(0, document.body.scrollHeight);") #only call function
                    time.sleep(sleep_between_interactions)

                    # build the google query

                search_url = "https://www.google.com/search?safe=off&site=&tbm=isch&source=hp&q={q}&oq={q}&gs_l=img" # url for images

                # load the page
                wd.get(search_url.format(q=query)) #serch images from browser

                image_urls = set()
                image_count = 0
                results_start = 0
                while image_count < max_links_to_fetch:
                    scroll_to_end(wd) # scroll down crusor from browser window

                    # get all image thumbnail results
                    thumbnail_results = wd.find_elements_by_css_selector("img.Q4LuWd") #tag name from class images
                    number_results = len(thumbnail_results)

                    print(f"Found: {number_results} search results. Extracting links from {results_start}:{number_results}")

                    for img in thumbnail_results[results_start:number_results]:
                        # try to click every thumbnail such that we can get the real image behind it
                        try:
                            img.click() # as we dont click on image it will not open ,as  we click we got url for that particullar image and we can download it
                            time.sleep(sleep_between_interactions)
                        except Exception:
                            continue

                        # extract image urls
                        actual_images = wd.find_elements_by_css_selector('img.n3VNCb') # 2 href contaion in one tag for one image

                        for actual_image in actual_images:
                            if actual_image.get_attribute('src') and 'http' in actual_image.get_attribute('src'):
                                image_urls.add(actual_image.get_attribute('src')) #url for paricular image

                        image_count = len(image_urls)

                        if len(image_urls) >= max_links_to_fetch:
                            print(f"Found: {len(image_urls)} image links, done!")
                            break
                    else:
                        print("Found:", len(image_urls), "image links, looking for more ...")
                        time.sleep(30)
                        return
                        load_more_button = wd.find_element_by_css_selector(".mye4qd")
                        if load_more_button:
                            wd.execute_script("document.querySelector('.mye4qd').click();")

                    # move the result startpoint further down
                    results_start = len(thumbnail_results)

                return image_urls




            def persist_image(folder_path:str,url:str, counter):
                try:
                    image_content = requests.get(url).content

                except Exception as e:
                    print(f"ERROR - Could not download {url} - {e}")

                try:
                    f = open(os.path.join(folder_path, 'jpg' + "_" + str(counter) + ".jpg"), 'wb')
                    f.write(image_content)
                    f.close()
                    print(f"SUCCESS - saved {url} - as {folder_path}")
                except Exception as e:
                    print(f"ERROR - Could not save {url} - {e}")

            target_path = './images'
            DRIVER_PATH = './chromedriver'
#def search_and_download(search_term: str, driver_path: str, target_path='./images', number_images=20):
            target_folder = os.path.join(target_path, '_'.join(search_term.lower().split(' ')))


            if not os.path.exists(target_folder):
                os.makedirs(target_folder)

            with webdriver.Chrome(executable_path=DRIVER_PATH) as wd: # only open browzer
                res = fetch_image_urls(search_term, number_images, wd=wd, sleep_between_interactions=0.5) # wd crome driv & sleeping time between images downloaded

            counter = 0
            for elem in res:
                persist_image(target_folder, elem, counter)
                counter += 1
            file_paths = []

            # crawling through directory and subdirectories
            for root, directories, files in os.walk(target_folder):
                for filename in files:
                    # join the two strings in order to form the full filepath.
                    filepath = os.path.join(root, filename)
                    file_paths.append(filepath)
            print(file_paths)

            download_file = search_term+".zip"

            for file_name in file_paths:
                with zipfile.ZipFile(download_file, 'w') as zip:
                # writing each file one by one
                    for file in file_paths:
                        zip.write(file)


            print('All files zipped successfully!')
            path=os.getcwd()

            print(download_file)

            fileobj = io.BytesIO()
            with zipfile.ZipFile(fileobj, 'w') as zip_file:
                zip_info = zipfile.ZipInfo(download_file)
                zip_info.date_time = time.localtime(time.time())[:6]
                zip_info.compress_type = zipfile.ZIP_DEFLATED
                with open(download_file, 'rb') as fd:
                    zip_file.writestr(zip_info, fd.read())
            fileobj.seek(0)

            # Changed line below
            return Response(fileobj.getvalue(),
                            mimetype='application/zip',
                            headers={'Content-Disposition': f'attachment;filename={download_file}'})
            #
            #
            #
            # #shutil.make_archive("target_folder", 'zip', 'target_folder')
            # return Response( headers={
            #     'Content-Type': 'application/zip',
            #     'Content-Disposition': 'attachment; filename=%s;' %download_file
            # })


        except Exception as e:
            print(e)
if __name__ == '__main__':

    app.run(debug=True)


# version:Version 94.0.4606.81
# How to execute this code
# Step 1 : pip install selenium. pillow, requests
# Step 2 : make sure you have chrome installed on your machine
# Step 3 : Check your chrome version ( go to three dot then help then about google chrome )
# Step 4 : Download the same chrome driver from here  " https://chromedriver.storage.googleapis.com/index.html "
# Step 5 : put it inside the same folder of this code


#DRIVER_PATH = './chromedriver'
#search_term = 'camel'
# num of images you can pass it from here  by default it's 10 if you are not passing
#number_images = 10
#search_and_download(search_term=search_term, driver_path=DRIVER_PATH)