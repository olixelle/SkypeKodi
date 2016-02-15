import xbmc
import xbmcaddon
import xbmcgui
from threading import Thread
import os
import time

__addon__ = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('name')
__icon__ = __addon__.getAddonInfo('icon')
__addonpath__    = __addon__.getAddonInfo('path').decode('utf-8')

__windowopen__ = True

#capture a couple of actions to close the window
ACTION_PREVIOUS_MENU = 10
ACTION_BACK = 92

#Globals
profileName = ""
profileHandle = ""
profileAvatarPath = ""
friends = []
wRinging = ""

#---------------------------------------------------------------------------------------------------------------------
#
class SkypeWindow(xbmcgui.WindowXML):
	def __init__( self, *args, **kwargs ):
		pass
	def onAction( self, action ):
		if action == ACTION_PREVIOUS_MENU or action == ACTION_BACK:
			self.close()
	def onClick(self, controlId):
		xbmc.log("Skype : action on click : " + str(controlId))
		if (controlId == 122):
			friendHandle = self.friendsList.getSelectedItem().getProperty('friend_handle')
			friendName = self.friendsList.getSelectedItem().getProperty('friend_name')
			friendAvatar = self.friendsList.getSelectedItem().getProperty('friend_avatar')
			callFriend(friendHandle, friendName, friendAvatar)
	def onInit(self):
		global profileName
		global profileAvatarPath
		global friends
		self.groupFriends = self.getControl(120)
		self.friendsList = self.getControl(122)
		self.userNameControl = self.getControl(1)
		self.avatarControl = self.getControl(2)
		self.updateUserInformation(profileName, profileAvatarPath)
		self.updateFriendsList(friends)
		xbmc.log("Skype : end of init")
	def onControl(self, control):
		xbmc.log("Skype : control on window : " + str(control.getId()))
	def updateUserInformation( self, name, avatar):
		self.userNameControl.setLabel(profileName)
		self.avatarControl.setImage(profileAvatarPath)
		xbmc.log("Skype : end of updateUserInformation")
	def updateFriendsList(self, friends):
		self.friendsList.reset()
		for f in friends:
			item = xbmcgui.ListItem(f.fullName)
			item.setIconImage(f.avatar)
			item.setProperty('friend_handle', f.handle)
			item.setProperty('friend_name', f.fullName)
			item.setProperty('friend_avatar', f.avatar)
			#item.setPath('Notification(header,item #1 clicked)')
			self.friendsList.addItem( item )
		xbmc.log("Skype : friends list updated")
		self.setFocusId(122)

#---------------------------------------------------------------------------------------------------------------------
#
class RingingWindow( xbmcgui.WindowXMLDialog ):
	def __init__( self, *args, **kwargs ): pass
	def onClick(self, controlId):
		xbmc.log("Skype : action on click : " + str(controlId))
		if (controlId == 133):
			skypeAction = self.getControl(133).getSelectedItem().getProperty('skype_action')
			xbmc.log("Skype : request action '" + skypeAction + "'")
			if (skypeAction == "accept"):
				runAccept()
			if (skypeAction == "refuse"):
				runRefuse()
	def ringing(self, friendName, friendAvatar, mode):
		self.show()
		self.actionsList = self.getControl(133)
		self.titleCtrl = self.getControl(132)
		self.avatarCtrl = self.getControl(131)
		self.friendNameCtrl = self.getControl(134)
		self.actionsList.reset()
		self.avatarCtrl.setImage(friendAvatar)
		if (mode == "incoming"):
			self.titleCtrl.setLabel("Incoming Call")

			item = xbmcgui.ListItem("Accept")
			item.setIconImage("accept.png")
			item.setProperty('skype_action', "accept")
			self.actionsList.addItem( item )

			item = xbmcgui.ListItem("Refuse")
			item.setIconImage("refuse.png")
			item.setProperty('skype_action', "refuse")
			self.actionsList.addItem( item )
		else:
			self.titleCtrl.setLabel("Calling...")

			item = xbmcgui.ListItem("Cancel")
			item.setIconImage("refuse.png")
			item.setProperty('skype_action', "refuse")
			self.actionsList.addItem( item )

		self.friendNameCtrl.setLabel(friendName)
		self.setFocusId(133)

#---------------------------------------------------------------------------------------------------------------------
#Read Profile information and update global vars
def loadProfile():
	global __addon__
	global profileName
	global profileHandle
	global profileAvatarPath

	filePath = __addon__.getSetting( 'skypexmlcontroller_var_path') + "skype2kodi\\profile.xml"
	xbmc.log("Skype : read profile from " + filePath)
	from xml.dom import minidom
	xmldoc = minidom.parse(filePath)
	profileName = xmldoc.getElementsByTagName('name')[0].childNodes[0].nodeValue
	profileAvatarPath = xmldoc.getElementsByTagName('avatar')[0].childNodes[0].nodeValue
	profileHandle = xmldoc.getElementsByTagName('handle')[0].childNodes[0].nodeValue

#---------------------------------------------------------------------------------------------------------------------
#
class skypeFriend:
	def __init__(self, eHandle, eFullName, eAvatarPath):
		self.handle = eHandle
		self.fullName = eFullName
		self.avatar = eAvatarPath


#---------------------------------------------------------------------------------------------------------------------
#
def loadFriends():
	global __addon__
	global friends
	filePath = __addon__.getSetting( 'skypexmlcontroller_var_path') + "skype2kodi\\friends.xml"
	xbmc.log("Skype : read friends from " + filePath)
	from xml.dom import minidom
	xmldoc = minidom.parse(filePath)
	friendNodes = xmldoc.getElementsByTagName('friend')
	for f in friendNodes:
		handle = f.getElementsByTagName('handle')[0].childNodes[0].nodeValue
		avatar = f.getElementsByTagName('avatar')[0].childNodes[0].nodeValue
		name = handle
		if len(f.getElementsByTagName('name')[0].childNodes) > 0:
			name = f.getElementsByTagName('name')[0].childNodes[0].nodeValue
		friends.append(skypeFriend(handle, name, avatar))
	xbmc.log("Skype : " + str(len(friends)) + " friends found")

#---------------------------------------------------------------------------------------------------------------------
#
def cleanUp():

	filePath = __addon__.getSetting( 'skypexmlcontroller_var_path') + "kodi2skype\\action.xml"
	if os.path.isfile(filePath):
		os.remove(filePath)

#---------------------------------------------------------------------------------------------------------------------
#
def checkCallStatus( name, skypeWindow ):
	time.sleep(10)
	filePath = __addon__.getSetting( 'skypexmlcontroller_var_path') + "skype2kodi\\call.xml"
	while __windowopen__ and (not xbmc.abortRequested):
		if os.path.isfile(filePath):
			from xml.dom import minidom
			xmldoc = minidom.parse(filePath)
			friendName = xmldoc.getElementsByTagName('name')[0].childNodes[0].nodeValue
			friendAvatar = xmldoc.getElementsByTagName('avatar')[0].childNodes[0].nodeValue
			callStatus = xmldoc.getElementsByTagName('status')[0].childNodes[0].nodeValue
			xbmc.log("Skype : call status is " + callStatus + " with " + friendName)

			if (callStatus == 'incoming'):
				wRinging.ringing(friendName, friendAvatar, 'incoming')
				#xbmc.executebuiltin('Notification(Skype,' + friendName + ' is calling !, 1000, ' + friendAvatar + ')')

			if (callStatus == 'outgoing'):
				wRinging.ringing(friendName, friendAvatar, 'outgoing')
				#xbmc.executebuiltin('Notification(Skype, Calling ' + friendName + ', 1000, ' + friendAvatar + ')')

			#if (callStatus == 'active'):
			#	xbmc.executebuiltin('Notification(Skype, Call active with ' + friendName + ', 1000, ' + friendAvatar + ')')

			if (callStatus == 'finished'):
				wRinging.close()
				os.remove(filePath)
				xbmc.executebuiltin('Notification(Skype, Call finished with ' + friendName + ', 3000, ' + friendAvatar + ')')


		time.sleep(2)

#---------------------------------------------------------------------------------------------------------------------
#
def callFriend( friendHandle, friendName, friendAvatar):
	xbmc.log("Skype : call friend " + friendHandle)
	wRinging.ringing(friendName, friendAvatar, 'outgoing')
	executeSkypeAction('call_friend', friendHandle)

#---------------------------------------------------------------------------------------------------------------------
#
def runAccept():
	executeSkypeAction('call_accept', '')

#---------------------------------------------------------------------------------------------------------------------
#
def runRefuse():
	executeSkypeAction('call_end', '')
	wRinging.close()

#---------------------------------------------------------------------------------------------------------------------
#
def executeSkypeAction(method, param):
	xbmc.log("Skype : execute action " + method + ' with param ' + param)
	xml = '<?xml version="1.0" encoding="utf-8"?><action><method>' + method + '</method><param>' + param + '</param></action>'
	filePath = __addon__.getSetting( 'skypexmlcontroller_var_path') + "kodi2skype\\action.xml"
	f =  open(filePath, "wb")
	f.write(xml)
	f.close()

#---------------------------------------------------------------------------------------------------------------------
#Main

xbmc.log("Skype : action " + __name__)
if ( __name__ == "__main__" ):
	if len(sys.argv) > 1:
		if sys.argv[1] == 'accept':
			runAccept()
		if sys.argv[1] == 'refuse':
			runRefuse()
	else:
		cleanUp()
		loadProfile()
		loadFriends()

		W = SkypeWindow( "skype-main.xml", __addonpath__ )
		wRinging = RingingWindow( "skype-ringing.xml", __addonpath__ )

		t1 = Thread( target=checkCallStatus,args=("thread skype.checkCallStatus", W) )
		t1.setDaemon( True )
		t1.start()

		__windowopen__ = True
		W.doModal()
		__windowopen__ = False
		del W
		del t1
