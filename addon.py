import xbmc
import xbmcaddon
import xbmcgui


__addon__ = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('name')
__icon__ = __addon__.getAddonInfo('icon')
__addonpath__    = __addon__.getAddonInfo('path').decode('utf-8')

#capture a couple of actions to close the window
ACTION_PREVIOUS_MENU = 10
ACTION_BACK = 92

#Globals
profileName = ""
profileHandle = ""
profileAvatarPath = ""
friends = []

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
	def onInit(self):
		global profileName
		global profileAvatarPath
		global friends
		self.updateUserInformation(profileName, profileAvatarPath)
		self.updateFriendsList(friends)
		xbmc.log("Skype : end of init")
	def onControl(self, control):
		xbmc.log("Skype : control on window : " + str(control.getId()))
	def updateUserInformation( self, name, avatar):
		self.userNameControl = self.getControl(1)
		self.userNameControl.setLabel(profileName)
		self.avatarControl = self.getControl(2)
		self.avatarControl.setImage(profileAvatarPath)
		xbmc.log("Skype : end of updateUserInformation")
	def updateFriendsList(self, friends):
		self.friendsList = self.getControl(3)
		self.friendsList.reset()
		for f in friends:
			item = xbmcgui.ListItem(f.fullName)
			item.setIconImage(f.avatar)
			#item.setPath('Notification(header,item #1 clicked)')
			self.friendsList.addItem( item )
		xbmc.log("Skype : friends list updated")


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
		name = avatar
		if len(f.getElementsByTagName('name')[0].childNodes) > 0:
			name = f.getElementsByTagName('name')[0].childNodes[0].nodeValue
		friends.append(skypeFriend(handle, name, avatar))
	xbmc.log("Skype : " + str(len(friends)) + " friends found")

#---------------------------------------------------------------------------------------------------------------------
#Main

if ( __name__ == "__main__" ):
	loadProfile()
	loadFriends()

	W = SkypeWindow( "skype-main.xml", __addonpath__ )
	W.doModal()
	del W
