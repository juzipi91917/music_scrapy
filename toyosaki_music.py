import json
import os
import requests
import jsonpath
import urllib.request
import concurrent.futures
from lxml import etree

headers = {
	'Host': 'www.kuwo.cn',
	'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/110.0',
	'Accept': 'application/json, text/plain, */*',
	'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
	'Accept-Encoding': 'gzip, deflate, br',
	'csrf': '3S4LCV6UB65',
	'Connection': 'keep-alive',
	'Referer': 'https://www.kuwo.cn/search/singers?key=%E9%99%B6%E5%96%86',
	'Cookie': 'kw_token=3S4LCV6UB65',
	'Sec-Fetch-Dest': 'empty',
	'Sec-Fetch-Mode': 'cors',
	'Sec-Fetch-Site': 'same-origin',
	'Pragma': 'no-cache',
	'Cache-Control': 'no-cache'
}


def list_handler(data: list):
	"""
	对列表中的元素进行处理，将列表中的"&nbsp;"和"&apos;"替换为空格和单引号

	Args:
		data (list): 需要处理的列表

	Returns:
		list: 处理后的列表
	"""
	for i in range(len(data)):
		data[i] = data[i].replace('&nbsp;', '').replace('&apos;', '')
	return data


def get_singer_info(singer_name):
	"""
	获取歌手信息

	Args:
		singer_name (str): 歌手名称

	Returns:
		tuple: 歌手名称列表和歌手ID列表
	"""
	# 构造歌手查询URL
	singer_url = f'https://www.kuwo.cn/api/www/search/searchArtistBykeyWord?key={singer_name}&pn=1&rn=30&httpsStatus=1&reqId=bcf54c80-c0cb-11ed-b23c-bdeb1a6b1e2e'
	# 发送请求，获取返回数据
	singer_json = requests.get(singer_url, headers=headers).text
	# 解析返回的JSON数据
	json_obj = json.loads(singer_json)
	# 从JSON数据中提取歌手名称列表和歌手ID列表
	singer_name_list = list_handler(jsonpath.jsonpath(json_obj, '$.data.list.*.name'))
	singer_id_list = jsonpath.jsonpath(json_obj, '$.data.list.*.id')
	# 返回歌手名称列表和歌手ID列表
	return singer_name_list, singer_id_list


def get_album_info(singer_id):
	page = 1
	album_name = []
	album_id = []
	while True:
		url = f'https://www.kuwo.cn/api/www/artist/artistAlbum?artistid={singer_id}&pn={page}&rn=20'
		page += 1
		album_json = requests.get(url=url, headers=headers).text
		json_obj = json.loads(album_json)
		album_list = jsonpath.jsonpath(json_obj, '$.data.albumList')[0]
		if len(album_list) != 0:
			album_name_t = [album['album'] for album in album_list]
			album_id_t = [album['albumid'] for album in album_list]
			list_handler(album_name_t)
			album_name.extend(album_name_t)
			album_id.extend(album_id_t)
		else:
			break
	return album_name, album_id


def get_songs_id_by_album_id(album_id):
	url = f'https://www.kuwo.cn/album_detail/{album_id}'
	response = requests.get(url=url, headers=headers).text
	tree = etree.HTML(response)
	song_id_list = [link.split('/')[2] for link in tree.xpath('//ul[@class="album_list"]/li//a[@class="name"]/@href')]
	song_name_list_t = tree.xpath('//ul[@class="album_list"]/li//a[@class="name"]/@title')
	return song_name_list_t, song_id_list


# def download_song(name_list, id_list, dir_name):
# 	if not id_list or not dir_name:
# 		return
# 	dir_path = f'./{singer}/{dir_name}'  # 可以提前定义文件夹路径
# 	if not os.path.exists(dir_path):
# 		os.mkdir(dir_path)
# 	for name, song_id in zip(name_list, id_list):  # 使用zip同时迭代两个列表
# 		url = f'https://www.kuwo.cn/api/v1/www/music/playUrl?mid={song_id}&type=convert_url&br=320kmp3'
# 		song_info = requests.get(url=url, headers=headers).json()  # 直接使用json方法返回解析后的json对象
# 		download_url = song_info['data']['url']  # 直接通过字典方式访问json对象
# 		file_path = f'{dir_path}/{name}.mp3'  # 可以提前定义文件路径
# 		urllib.request.urlretrieve(url=download_url, filename=file_path)
# 		print(f'{name} 下载完成')

def download_song(name, song_id, dir_path):
	url = f'https://www.kuwo.cn/api/v1/www/music/playUrl?mid={song_id}&type=convert_url&br=320kmp3'
	song_info = requests.get(url=url, headers=headers).json()
	download_url = song_info['data']['url']
	file_path = f'{dir_path}/{name}.mp3'
	if os.path.exists(file_path):
		print(f'歌曲{name}已存在, 跳过下载')
		return
	urllib.request.urlretrieve(url=download_url, filename=file_path)
	print(f'{name} 下载完成')


def download_songs(name_list, id_list, dir_name):
	if not id_list or not dir_name:
		return
	dir_path = f'./{singer}/{dir_name}'
	if not os.path.exists(dir_path):
		os.mkdir(dir_path)
	with concurrent.futures.ThreadPoolExecutor() as executor:
		futures = [executor.submit(download_song, name, song_id, dir_path) for name, song_id in zip(name_list, id_list)]
	for future in concurrent.futures.as_completed(futures):
		try:
			future.result()
		except Exception as exc:
			print(f'generated an exception: {exc}')


def get_singer_name():
	singer = input('根据歌手专辑进行下载, 输入歌手名称:')
	if not os.path.exists('./' + singer):
		os.mkdir('./' + singer)
	return singer


def select_singer(singer_name_list):
	print('搜索结果如下:')
	for index in range(len(singer_name_list) // 2):
		print(str(index + 1) + '. ' + singer_name_list[index])
	choice = int(input('请输入你需要下载的歌手的序号:')) - 1
	return choice


def select_album(album_name):
	print('以下是该歌手的专辑信息')
	for index in range(len(album_name)):
		print(str(index + 1) + '. ' + album_name[index])
	print('即将开始下载')


def download_by_album(singer_id_list, choice):
	album_name, album_id = get_album_info(singer_id_list[choice])
	for index in range(len(album_id)):
		song_name_list, song_id_list = get_songs_id_by_album_id(album_id[index])
		download_songs(song_name_list, song_id_list, album_name[index])


if __name__ == '__main__':
	singer = get_singer_name()
	singer_name_list, singer_id_list = get_singer_info(singer)
	choice = select_singer(singer_name_list)
	select_album(get_album_info(singer_id_list[choice])[0])
	download_by_album(singer_id_list, choice)
