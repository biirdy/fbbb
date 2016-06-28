
import subprocess
import cv2
import array
import numpy
import time
import threading
import Queue


from cv2 import cv

def screen_loop(q, ball, hoop):

	ball_rows, ball_cols = ball.shape[:2]
	hoop_rows, hoop_cols = hoop.shape[:2]	

	while True:
		time1 = time.time()

		screen = get_screen()
		ball_x, ball_y, hoop_x, hoop_y = get_loc(screen, ball, hoop)

		last_stats = q.get()

		if last_stats['time'] == 0:
			q.put({'time' : time1, 'ball_x' : ball_x, 'ball_y' : ball_y, 'hoop_x' : hoop_x, 'hoop_y' : hoop_y, 'hoop_speed' : 0, 'direction' : 0})
		else:
			print last_stats

			# nearing left
			#if last_stats['hoop_x'] < (hoop_cols/2) + 220 and last_stats['hoop_speed'] < 0:
				# add two distances 
				#hoop_x -> 0 && 0 -> hoop_x
				

			#	hoop_speed = (last_stats['hoop_x'] + hoop_x - hoop_cols) / (time1 - last_stats['time'])
			# nearing right
			#elif last_stats['hoop_x'] > 1080 - ((hoop_cols/2) + 220) and last_stats['hoop_speed'] > 0:

			#	print('Nearing right')
			#	print('last x ' + str(last_stats['hoop_x']))
			#	print('x ' + str(hoop_x))
			#	print('total distance ' + str((1080 - last_stats['hoop_x']) + (1080 - hoop_x)))
			#	print('total centre distance ' + str((1080 - last_stats['hoop_x']) + (1080 - hoop_x) - hoop_cols))

				# add two distances - negative 
				#hoop_x -> 1080 && 1080 -> hoop_x
			#	hoop_speed = -((1080 - last_stats['hoop_x']) + (1080 - hoop_x)) - hoop_cols / (time1 - last_stats['time'])
			# mid screen
			#else:
				# simple - distance / time 
			hoop_speed = (hoop_x - last_stats['hoop_x']) / (time1 - last_stats['time'])
			
			# direction
			# static
			if hoop_speed == 0:
				direction = 0
			# change direction
			elif hoop_speed < 220 or hoop_speed > -220:
				direction = -1 if last_stats['hoop_speed'] > 0 else 1	
			# same direction
			else:
				direction = -1 if hoop_speed < 0 else 1

			q.put({'time' : time1, 'ball_x' : ball_x, 'ball_y' : ball_y, 'hoop_x' : hoop_x, 'hoop_y' : hoop_y, 'hoop_speed' : hoop_speed, 'direction' : direction})
			
			#cv2.imwrite('test%d.png' % hoop_x, screen)
			#draw_loc(screen, ball_x, ball_y, ball_cols, ball_rows, hoop_x, hoop_y, hoop_cols, hoop_rows)


#
#
def predict(hoop_x, direction, time1, hoop):

	if direction == 0:
		return hoop_x

	age = (time.time() - time1)
	delta = age * 220

	if direction == 1:

		if hoop_x > (1080 - (hoop_cols/2)):
			return delta - ((1080 - (hoop_cols/2)) - hoop_x)
		else:
			return hoop_x + delta

	elif direction == -1:

		if hoop_x < (hoop_cols/2):
			return delta - (hoop_x - (hoop_cols/2)) 
		else:
			return hoop_x - delta

#
#
def send_swipe(x1, y1, x2, y2):
	adb = subprocess.call(("adb", "shell", "input", "touchscreen", "swipe", str(x1), str(y1), str(x2), str(y2)))

#
#
def get_screen():
	#screen = open("screen.png", "w")
	#adb = subprocess.Popen(("adb", "shell", "screencap", "-p"), universal_newlines=True, stdout=subprocess.PIPE)
	#subprocess.call(("perl", "-p", "rep.pl"), stdin=adb.stdout, stdout=screen)
	#screen.close()

	adb 	= subprocess.Popen(("adb", "shell", "screencap", "-p"), stdout=subprocess.PIPE)
	screen 	= subprocess.check_output(("perl", "-p", "rep.pl"), stdin=adb.stdout)
	screen_array = numpy.fromstring(screen, numpy.uint8) 
	#screen.seek(0)
	#screen_array = np.asarray(bytearray(screen.read()), dtype=np.uint8)
	return cv2.imdecode(screen_array, cv2.CV_LOAD_IMAGE_COLOR)

#
#
def get_loc(screen_shot, ball, hoop):

	method = cv.CV_TM_SQDIFF_NORMED

	ball_result = cv2.matchTemplate(ball, screen_shot, method)
	hoop_result = cv2.matchTemplate(hoop, screen_shot, method)

	mn,_,ball_loc,_ = cv2.minMaxLoc(ball_result)
	mn,_,hoop_loc,_ = cv2.minMaxLoc(hoop_result)

	# coordinates
	ball_x, ball_y = ball_loc
	hoop_x, hoop_y = hoop_loc

	# sizes
	ball_rows, ball_cols = ball.shape[:2]
	hoop_rows, hoop_cols = hoop.shape[:2]	

	return (ball_x + (ball_cols/2), ball_y + (ball_cols/2), hoop_x + (hoop_cols/2), hoop_y + hoop_rows)

#
#
def draw_loc(screen_shot, ball_x, ball_y, ball_cols, ball_rows, hoop_x, hoop_y, hoop_cols, hoop_rows):
	cv2.rectangle(screen_shot, (ball_x, ball_y), (ball_x + ball_cols, ball_y + ball_rows), (0,0,255), 2)
	cv2.rectangle(screen_shot, (hoop_x, hoop_y), (hoop_x + hoop_cols, hoop_y + hoop_rows), (0,0,255), 2)

	# half the resolution
	display = cv2.resize(screen_shot, (0,0), fx=0.5, fy=0.5) 

	cv2.namedWindow('display', flags=cv2.WINDOW_OPENGL)
	cv2.imshow('display', display)

	cv2.waitKey(0)

	cv2.destroyAllWindows()

ball = cv2.imread('ball.png')
hoop = cv2.imread('hoop.png')

ball_rows, ball_cols = ball.shape[:2]
hoop_rows, hoop_cols = hoop.shape[:2]	

q = Queue.Queue(1)
q.put({'time' : 0})

thread = threading.Thread(target=screen_loop, args=(q, ball, hoop))
thread.deamon = True
thread.start()

time.sleep(5)

while(1):
	time.sleep(1)
	#inp = raw_input("Calculate...")

	#time1 = time.time()
	
	#print("Getting first location")
	#screen = get_screen()
	#ball_x, ball_y, hoop_x, hoop_y = get_loc(screen, ball, hoop)

	#time2 = time.time()
	#first_duration = (time2 - time1)*1000
	#print '%0.3f ms' % first_duration

	#print("Getting second location")
	#screen = get_screen()
	#ball_x2, ball_y2, hoop_x2, hoop_y2 = get_loc(screen, ball, hoop)

	#time3 = time.time()
	#second_duration = (time2 - time1)*1000
	#print '%0.3f ms' % second_duration


	#hoop_diff = hoop_x2 - hoop_x 
	#print 'Hoop pixel diff ' + str(hoop_diff)

	#hoop_speed = (1000 / first_duration) * hoop_diff
	#print 'Hoop speed ' + str(hoop_speed) + 'p/s' 

	#time3 = time.time()
	#print '%0.3f ms' % ((time3 - time2)*1000)
	#delta = 170 * (first_duration/1000) + 100
	#print 'Delta ' + str(delta)

	stats = q.get()
	q.put(stats)

	if stats['ball_y'] == 1729: 

		print("Sending swipe")
		send_swipe(stats['ball_x'], stats['ball_y'], predict(stats['hoop_x'], stats['direction'], stats['time'], hoop) , stats['hoop_y'])




	#time4 = time.time()
	#print '%0.3f ms' % ((time4 - time3)*1000)
	
