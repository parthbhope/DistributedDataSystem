from flask import Flask,request,redirect,url_for
from flask import render_template
import os
import subprocess
import threading
import time
import sys
app = Flask(__name__)
sys.path.append('/home/ritesh/subjects/DDS/Assignment4/flaskApp/DDSgo/raft-samples')

initateCmd = ["SERVER_PORT=2221 RAFT_NODE_ID=node1 RAFT_PORT=1111 RAFT_VOL_DIR=node_1_data go run ysf/raftsample/cmd/api",
			"SERVER_PORT=2222 RAFT_NODE_ID=node2 RAFT_PORT=1112 RAFT_VOL_DIR=node_2_data go run ysf/raftsample/cmd/api",
			 "SERVER_PORT=2223 RAFT_NODE_ID=node3 RAFT_PORT=1113 RAFT_VOL_DIR=node_3_data go run ysf/raftsample/cmd/api"
			]


votingCmd = [ ''' 
					curl --location --request POST 'localhost:2221/raft/join' \
					--header 'Content-Type: application/json' \
					--data-raw '{
						"node_id": "node_2", 
						"raft_address": "127.0.0.1:1112"
					}' ''',

				''' 
					curl --location --request POST 'localhost:2221/raft/join' \
					--header 'Content-Type: application/json' \
					--data-raw '{
						"node_id": "node_3", 
						"raft_address": "127.0.0.1:1113"
					}' ''',
			  
			]

nodeDict = []

def runCommand(cmd,t):
	if t == 'e':
		os.system(initateCmd[int(cmd)])
	elif t == 'v':
		os.system(votingCmd[int(cmd)])
	else:
		p = os.popen(cmd).read()
		return p

def getLeader():
	global nodeDict
	for node in nodeDict:
		if node['leader']:
			return node
	return None

def createCluster():
	global nodeDict
	t1 = threading.Thread(target=runCommand,args=('0',"e")).start()
	t2 = threading.Thread(target=runCommand,args=('1',"e")).start()
	t3 = threading.Thread(target=runCommand,args=('2',"e")).start()

	time.sleep(10)
	voting1 = runCommand('0','v')
	voting2 = runCommand('1','v')


	nodeDict += [{'serverPort' : '2221', 'raftPort' : '1111' , 'leader' : True,'nodeId' : 'node_1' }]
	nodeDict += [{'serverPort' : '2222', 'raftPort' : '1112' , 'leader' : False,'nodeId' : 'node_2'}]
	nodeDict += [{'serverPort' : '2223', 'raftPort' : '1113' , 'leader' : False ,'nodeId' : 'node_3'}]





@app.route('/home')
def home():
	global nodeDict
	d = {}
	try:
		msg  = request.args['msg']
		print(msg,"weriwoih")
		return render_template("home.html",option_list=nodeDict,msg=msg)
	except Exception as e:
		print(e,"wpwpwpwpwpwpwp")
		pass
	return render_template("home.html",option_list=nodeDict)

@app.route('/joinCluster',methods=["POST","GET"])
def joinCluster():
	'''
	  req - leader ip known
	'''
	global nodeDict
	if request.method == "POST":
		data = request.form.to_dict(flat=False)
		print(data)
		leaderNode = getLeader()
		cmd2 = ''' curl --location --request POST 'localhost:{leaderIp}/raft/join'  --header 'Content-Type: application/json' --data-raw '{{ "node_id": "{node_id}" , "raft_address": "127.0.0.1:{raftPort}" }}' ''' .format(leaderIp=leaderNode['serverPort'], node_id = data['nodeid'][0] , raftPort = data['raftport'][0])
		cmd1 = "SERVER_PORT={serverport} RAFT_NODE_ID={nodeid} RAFT_PORT={raftport} RAFT_VOL_DIR={nodedata} go run ysf/raftsample/cmd/api".format(serverport=data['serverport'][0],nodeid=data['nodeid'][0],raftport=data['raftport'][0],nodedata=data['nodeid'][0]+'_data')
		print(cmd1)
		print(cmd2)
		new_thread = threading.Thread(target=runCommand,args=(cmd1,"n")).start()
		time.sleep(3)
		runCommand(cmd2,'n')
		nodeDict += [{'serverPort' : data['serverport'][0], 'raftPort' : data['raftport'][0] , 'leader' : False,'nodeId' : data['nodeid'][0] }]
		return redirect('http://localhost:5000/home')
	else:
		return render_template("home.html")

@app.route('/leaveCluster')
def leaveCluster():
   return 'Hello'

@app.route('/setKey',methods=["POST","GET"])
def setKey():
	'''
	  req - leader ip needs ip to be known
	'''
	if request.method == "POST":
		data = request.form.to_dict(flat=False)
		print(data)
		leaderNode = getLeader()
		cmd = ''' curl --location --request POST 'http://localhost:{leaderIp}/store' --header 'Content-Type: application/json' --data-raw '{{ "key": "{key}", "value": "{value}" }}' '''.format(leaderIp=leaderNode['serverPort'],key=data['key'][0],value=data['value'][0])
		runCommand(cmd,'n')
		return redirect("http://localhost:5000/home")
	else:
		return render_template("home.html")

 

@app.route('/getKey',methods=["POST","GET"])
def getKey():
	if request.method == "POST":
		data = request.form.to_dict(flat=False)
		print(data)
		cmd = ''' curl --location --request GET 'http://localhost:{}/store/{}' '''.format(data['option'][0],data['key'][0])
		p  = str(runCommand(cmd,'n'))
		return redirect(url_for('.home',msg=p))
	else:
		return render_template('home.html',msg=p)


@app.route('/deleteKey')
def deleteKey():
	'''
	  req - leader ip needs ip to be known
	'''
	if request.method == "POST" :
		data = request.form.to_dict(flat=False)
		leaderNode = getLeader()
		cmd = '''curl --location --request DELETE 'http://localhost:{}/store/{}' '''.format(leaderNode['serverPort'][0],data['key'][0])
		runCommand(cmd,'n')
		return redirect('http://localhost:5000/home')


if __name__ == '__main__':
	createCluster()
	app.run(debug=True)