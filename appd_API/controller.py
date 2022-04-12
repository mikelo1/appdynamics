from .appdRESTfulAPI import RESTfulAPI
from .applications import ApplicationDict
from .dashboards import DashboardDict
from .rbac import RBACDict, AccountDict
from .settings import ConfigurationDict
from .nodes import NodeDict, TierDict
from .transactiondetection import DetectionruleDict
from .businesstransactions import BusinessTransactionDict
from .backends import BackendDict, EntrypointDict
from .healthrules import HealthRuleDict
from .policies import PolicyDict
from .actions import ActionDict
from .schedules import ScheduleDict
from .events import EventDict, ErrorDict, MetricDict
from .snapshots import SnapshotDict

class Controller:
    RESTfulAPI      = None
    dashboards      = None
    users = account = None
    config          = None
    applications = tiers = nodes = None
    transactiondetection = businesstransactions = backends = entrypoints = None
    healthrules = policies = actions = schedules = None
    events = metrics = errors = snapshots = None
    entityDict =  {}

    def __init__(self, appD_Config, basicAuth=None):
        self.RESTfulAPI   = RESTfulAPI(appD_Config,basicAuth)
        self.applications = ApplicationDict(self)
        self.dashboards   = DashboardDict(self)
        self.users        = RBACDict(self)
        self.account      = AccountDict(self)
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
        self.metrics   = MetricDict(self)
        self.snapshots = SnapshotDict(self)
        self.entityDict =  { 'applications': {'object': self.applications, 'class': ApplicationDict },
                             'dashboards':   {'object': self.dashboards, 'class': DashboardDict },
                             'config':       {'object': self.config, 'class': ConfigurationDict },
                             'users':        {'object': self.users, 'class': RBACDict },
                             'account':      {'object': self.account, 'class': AccountDict },
                             'tiers':                {'object': self.tiers, 'class': TierDict },
                             'nodes':                {'object': self.nodes, 'class': NodeDict },
                             'detection-rules':      {'object': self.transactiondetection, 'class': DetectionruleDict },
                             'businesstransactions': {'object': self.businesstransactions, 'class': BusinessTransactionDict },
                             'backends':             {'object': self.backends, 'class': BackendDict },
                             'entrypoints':          {'object': self.entrypoints, 'class': EntrypointDict },
                             'healthrules': {'object': self.healthrules, 'class': HealthRuleDict },
                             'policies':    {'object': self.policies, 'class': PolicyDict },
                             'actions':     {'object': self.actions, 'class': ActionDict },
                             'schedules':   {'object': self.schedules, 'class': ScheduleDict },
                             'healthrule-violations': {'object': self.events, 'class': EventDict },
                             'snapshots':             {'object': self.snapshots, 'class': SnapshotDict },
                             'allothertraffic':       {'object': self.snapshots, 'class': SnapshotDict },
                             'errors':                {'object': self.errors, 'class': ErrorDict },
                             'metrics':               {'object': self.metrics, 'class': MetricDict }
                           }


    def __str__(self):
        return "({0},{1})".format(self.__class__.__name__,len(self.entityDict))

    ###### FROM HERE PUBLIC FUNCTIONS ######

    def get_entityObject(self,entity_name=None,entity_class=None):
        if entity_name is not None:
            return self.entityDict[entity_name]['object']
        elif entity_class:
            return [ self.entityDict[entity]['object'] for entity in self.entityDict if self.entityDict[entity]['class'].__name__ == entity_class][0]
        return None

# Global object that works as Singleton
#controller = Controller()