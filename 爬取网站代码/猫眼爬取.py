import requests
from bs4 import BeautifulSoup
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from PIL import Image
import cv2
from selenium.webdriver import ActionChains
from io import BytesIO

class MaoYanCode:
    def __init__(self, browser):
        self.browser = browser
        self.wait = WebDriverWait(browser, 10)


    def bg_img_src(self):
        # 定位背景图
        bg_img_element = self.wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@class="tc-bg"]/img')))
        bg_img_src = bg_img_element.get_attribute('src')
        return bg_img_src

    def jpp_img_src(self):
        # 定位缺块
        target_img_element = self.wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@class="tc-jpp"]/img')))
        target_img_src = target_img_element.get_attribute('src')
        return target_img_src

    def get_img(self):
        # 获取背景和缺块图片
        bg_src = self.bg_img_src()
        jpp_src = self.jpp_img_src()
        response1 = requests.get(bg_src)
        image1 = Image.open(BytesIO(response1.content))
        image1.save('bg_img.png')

        response2 = requests.get(jpp_src)
        image2 = Image.open(BytesIO(response2.content))
        image2.save('jpp_img.png')
        return image1, image2

    def slider_element(self):
        # 定位滑块
        time.sleep(2)
        slider = self.wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@class="tc-drag-thumb"]')))
        return slider

    def get_gap(self):
        # 识别缺口
        bg_img = cv2.imread("bg_img.png")
        tp_img = cv2.imread("jpp_img.png")

        bg_edge = cv2.Canny(bg_img, 100, 200)
        tp_edge = cv2.Canny(tp_img, 100, 200)

        bg_pic = cv2.cvtColor(bg_edge, cv2.COLOR_GRAY2RGB)
        tp_pic = cv2.cvtColor(tp_edge, cv2.COLOR_GRAY2RGB)

        res = cv2.matchTemplate(bg_pic, tp_pic, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

        height, width = tp_pic.shape[:2]
        tl = max_loc
        cv2.rectangle(bg_img, tl, (tl[0] + width - 15, tl[1] + height - 15), (0, 0, 255), 2)
        cv2.imwrite('../猫眼爬取/result.png', bg_img)
        return tl[0]

    def get_track(self, distance):
        # 构造移动轨迹
        track = []
        current = 0
        mid = distance * 4 / 5
        t = 0.2
        v = 0

        while current < distance:
            if current < mid:
                a = 5
            else:
                a = -3
            v0 = v
            v = v0 + a * t
            move = v0 * t + 1 / 2 * a * t * t
            current += move
            track.append(round(move))
        return track

    def move_to_gap(self, slider, track):
        # 移动滑块
        ActionChains(self.browser).click_and_hold(slider).perform()
        for x in track:
            ActionChains(self.browser).move_by_offset(xoffset=x, yoffset=0).perform()
        time.sleep(0.5)
        ActionChains(self.browser).release().perform()

    def solve_captcha(self):
        try:
            # 切换到验证码 iframe
            iframe = self.wait.until(
                EC.presence_of_all_elements_located((By.TAG_NAME, 'iframe'))
            )
            self.wait.until(
                EC.frame_to_be_available_and_switch_to_it(iframe[0])
            )

            # 获取图片并进行处理
            self.get_img()
            slider = self.slider_element()
            gap = self.get_gap()
            gap_end = int((gap - 40) / 2)
            gap_end -= 10
            track = self.get_track(gap_end)
            self.move_to_gap(slider, track)

            # 等待验证成功
            time.sleep(10)

            # 切换回验证码 iframe 进行进一步处理
            iframe = self.wait.until(
                EC.presence_of_all_elements_located((By.TAG_NAME, 'iframe'))
            )
            self.wait.until(
                EC.frame_to_be_available_and_switch_to_it(iframe[0])
            )
            self.get_img()

        except Exception as e:
            # 捕获异常并输出错误信息
            # print(f"Error occurred: {e}")
            return  # 出现异常时退出函数

def scrape_movies(url, headers):
    # 配置Selenium WebDriver
    options = webdriver.EdgeOptions()
    options.add_argument("--headless")  # 无头模式（可选）--start-maximized，--headless
    browser = webdriver.Edge(options=options)
    wait = WebDriverWait(browser, 3)

    # 实例化 MaoYanCode
    mao_yan_code = MaoYanCode(browser)

    # 打开网页
    browser.get(url)
    time.sleep(1)
    # 解决滑块验证码
    mao_yan_code.solve_captcha()

    # 发起请求获取网页内容
    response = requests.get(url, headers=headers)
    html_content = response.text
    # print(html_content)

    # 创建BeautifulSoup对象来解析HTML
    soup = BeautifulSoup(html_content, "html.parser")

    # 查找所有电影项
    movie_items = soup.find_all("div", class_="movie-item film-channel")

    # 打开CSV文件准备写入电影信息
    with open("movies_my(9_120).csv", mode="a", newline="", encoding="utf-8") as file:
        csv_writer = csv.writer(file)
        # 写入CSV文件的标题行
        csv_writer.writerow(["影片名称", "评分", "类型", "主演", "上映日期", "图片URL"])

        for item in movie_items:
            # 提取影片名称
            title_tag = item.find("span", class_="name")
            title = title_tag.text.strip() if title_tag else "N/A"

            # 提取评分
            rating_tag = item.find("span", class_="score channel-detail-orange")
            rating = rating_tag.text.strip() if rating_tag else "暂无评分"

            # 提取电影详细信息
            hover_info = item.find("div", class_="movie-item-hover")
            if hover_info:
                # 提取类型
                type_text = "N/A"
                for div in hover_info.find_all("div", class_="movie-hover-title"):
                    if "类型:" in div.get_text():
                        type_text = div.get_text(strip=True).split("类型:")[1].strip()
                        break

                # 提取主演
                cast_text = "N/A"
                for div in hover_info.find_all("div", class_="movie-hover-title"):
                    if "主演:" in div.get_text():
                        cast_text = div.get_text(strip=True).split("主演:")[1].strip()
                        break

                # 提取上映日期
                date_text = "N/A"
                for div in hover_info.find_all("div", class_="movie-hover-title"):
                    if "上映时间:" in div.get_text():
                        date_text = div.get_text(strip=True).split("上映时间:")[1].strip()
                        break

            else:
                type_text, cast_text, date_text = "N/A", "N/A", "N/A"

            # 提取图片 URL
            image_tag = item.find("img", class_="movie-hover-img")
            image_url = image_tag["src"].strip() if image_tag and "src" in image_tag.attrs else "N/A"

            # 写入电影信息到 CSV 文件
            csv_writer.writerow([title, rating, type_text, cast_text, date_text, image_url])

    # print("电影信息已写入到 movies_my(9_120).csv。")

    # 关闭浏览器
    browser.quit()

if __name__ == '__main__':
    base_url = "https://www.maoyan.com/films"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
        'Cookies': 'your_cookies_here',  # 这里需要填写实际的Cookies值
        'Referer': 'https://passport.maoyan.com/'
    }

    # 创建 CSV 文件准备写入电影信息
    with open("movies_my(9_120).csv", mode="w", newline="", encoding="utf-8") as file:
        csv_writer = csv.writer(file)
        # 写入CSV文件的标题行
        csv_writer.writerow(["影片名称", "评分", "类型", "主演", "上映日期", "图片URL"])

    # 遍历所有 yearId 和 offset
    for year_id in range(1,25):  # yearId 从 1 到 24
        for offset in range(0, 2000, 30):  # offset 从 0 到 2000，步长为 30
            url = f"{base_url}?yearId={year_id}&showType=3&offset={offset}"
            # print(f"Fetching URL: {url}")
            scrape_movies(url, headers)
            print(f"已完成{year_id}——{offset}的爬取。")
