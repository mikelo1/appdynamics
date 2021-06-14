from applications import ApplicationDict
from dashboards import DashboardDict
from rbac import RBACDict
from settings import ConfigurationDict

class Controller:
	applications = None
	dashboards   = None
	users        = None
	config       = None

	def __init__(self):
		self.applications = ApplicationDict(self)
		self.dashboards   = DashboardDict()
		self.users        = RBACDict()
		self.config       = ConfigurationDict()

	def __str__(self):
		return "({0},{1},{2},{3})".format(self.applications,self.dashboards,self.users,self.config)

# Global object that works as Singleton
controller = Controller()