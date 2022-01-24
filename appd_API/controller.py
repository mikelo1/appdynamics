from .appdRESTfulAPI import RESTfulAPI
from .applications import ApplicationDict
from .dashboards import DashboardDict
from .rbac import RBACDict
from .settings import ConfigurationDict
from .nodes import NodeDict, TierDict
from .transactiondetection import DetectionruleDict
from .businesstransactions import BusinessTransactionDict
from .backends import BackendDict, EntrypointDict
from .healthrules import HealthRuleDict
from .policies import PolicyDict
from .actions import ActionDict
from .schedules import ScheduleDict
from .events import EventDict, ErrorDict
from .snapshots import SnapshotDict

class Controller:
    RESTfulAPI   = None
    applications = None
    dashboards   = None
    users        = None
    config       = None
    nodes        = None
    transactiondetection = businesstransactions = backends = entrypoints = None
    healthrules = policies = actions = schedules = None
    events = errors = snapshots = None

    def __init__(self, appD_Config, basicAuth=None):
        self.RESTfulAPI   = RESTfulAPI(appD_Config,basicAuth)
        self.applications = ApplicationDict(self)
        self.dashboards   = DashboardDict(self)
        self.users        = RBACDict(self)
        self.config       = ConfigurationDict(self)
        self.tiers                = TierDict(self)
        self.nodes                = NodeDict(self)
        self.transactiondetection = DetectionruleDict(self)
        self.businesstransactions = BusinessTransactionDict(self)
        self.backends             = BackendDict(self)
        self.entrypoints          = EntrypointDict(self)
        self.healthrules = HealthRuleDict(self)
        self.policies    = PolicyDict(self)
        self.actions     = ActionDict(self)
        self.schedules   = ScheduleDict(self)
        self.events    = EventDict(self)
        self.errors    = ErrorDict(self)
        self.snapshots = SnapshotDict(self)

    def __str__(self):
        return "({0},{1})".format(self.applications,self.config)

# Global object that works as Singleton
#controller = Controller()