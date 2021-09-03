import time
from typing import List, Optional, Union
from parsed_objects import ParsedHypervisor

# NOTE: when adding new class, add to Union[...] of QueueItem constructor to help IDE typing


class StatusItem:
    def __init__(self, start_time: float = 0.0, running_on: str = "", iteration: int = -1):
        self.start_time: float = start_time
        self.completed: bool = False
        self.running_on: str = running_on
        self.iteration = iteration

    def print_data(self) -> str:
        """Use this method for spilling the contents of an instance."""
        s = "StatusItem:\n"
        s += f"\tstart_time: {self.start_time}\n"
        s += f"\tcompleted: {self.completed}\n"
        s += f"\trunning_on: {self.running_on}\n"
        s += f"\titeration: {self.iteration}\n"
        return s


class OutputItem:

    def __init__(self, new_output: str, iteration_output: int = -1, testbed_output: bool = False):
        self.new_output = new_output
        self.iteration_output: int = iteration_output
        self.testbed_output: bool = testbed_output

    def print_data(self) -> str:
        """Use this method for spilling the contents of an instance."""
        s = "OutputItem:\n"
        s += f"\tnew_output: {self.new_output}\n"
        s += f"\titeration_output: {self.iteration_output}\n"
        s += f"\ttestbed_output: {self.testbed_output}\n"
        return s


class TestbedRequestItem:

    def __init__(self, function_name: str, iteration: int = -1, node: str = ""):

        self.function_name: str = function_name
        self.iteration: int = iteration
        self.node: str = node

    def print_data(self):
        s = "TestbedRequestItem:\n"
        s += f"\tfunction_name: {self.function_name}\n"
        return s


class ControllerRequestItem:

    def __init__(self, function_name: str):

        self.function_name: str = function_name

    def print_data(self):
        s = "ControllerRequestItem:\n"
        s += f"\tfunction_name: {self.function_name}\n"
        return s


class IterationRequestItem:

    def __init__(self, function_name: str):

        self.function_name: str = function_name

    def print_data(self) -> str:
        return "NOT DEFINED"

class AgentControlItem:

    def __init__(self, for_node: str, reset: bool = False, kill: bool = False):

        self.for_node: str = for_node

        self.reset = reset
        self.kill = kill

    def print_data(self) -> str:
        return "NOT DEFINED"

class StageItem:

    def __init__(self, new_stage: int, new_iteration: int):
        self.new_stage = new_stage
        self.new_iteration = new_iteration
        self.stage_complete = False
        self.from_gui_agent = False

    def print_data(self) -> str:
        """Use this method for spilling the contents of an instance."""
        s = "StageItem:\n"
        s += f"\tnew_stage: {self.new_stage}\n"
        s += f"\tnew_iteration: {self.new_iteration}\n"
        s += f"\tstage_complete: {self.stage_complete}\n"
        s += f"\tfrom_gui_agent: {self.from_gui_agent}\n"
        return s


class GUIAgentItem:
    def __init__(self, id: str, gui_type: str, command: str, remote_ip: str, remote_port: int, remote_user: str,
                 remote_password: str, compute_node_ip: str, compute_node_port: int, compute_node_user: str,
                 node: Optional[ParsedHypervisor], iteration: int = -1, action_index: int = -1):
        self.id: str = id
        self.gui_type: str = gui_type
        self.command: str = command
        self.remote_ip: str = remote_ip
        self.remote_port: int = int(remote_port)
        self.remote_user: str = remote_user
        self.remote_password: str = remote_password

        self.compute_node_ip: str = compute_node_ip
        self.compute_node_port: int = compute_node_port
        self.compute_node_user: str = compute_node_user

        self.node: Optional[ParsedHypervisor] = node

        # Added to remove the complexity of populating the action_definitions dictionary in WebController (TLT).
        self.iteration = iteration
        self.action_index = action_index

        # TODO: for now, this is left up to system running GUIAgent (typically as normally user);
        #  could identify only filename and leave directory to GUIAgent setting
        # self.compute_node_keyfile: str

        self.kill_guis: bool = False

        self.complete: bool = False

    def print_data(self) -> str:
        s = "GUIAgentItem:\n"
        s += f"\tid: {self.id}\n"
        s += f"\tgui_type: {self.gui_type}\n"
        s += f"\tcommand: {self.command}\n"
        s += f"\tremote_ip: {self.remote_ip}\n"
        s += f"\tremote_port: {self.remote_port}\n"
        s += f"\tremote_user: {self.remote_user}\n"
        s += f"\tremote_password: {self.remote_password}\n"
        s += f"\tcompute_node_ip: {self.compute_node_ip}\n"
        s += f"\tcompute_node_port: {self.compute_node_port}\n"
        s += f"\tcompute_node_user: {self.compute_node_user}\n"
        s += f"\titeration: {self.iteration}\n"
        s += f"\taction_index: {self.action_index}\n"
        return s


class LoggingItem:
    def __init__(self, message: str, level: int):
        self.message = message
        self.level = level


class MinimegaItem:
    """This class is the QueueItem.item class that communicates command string and functions to call in
    MinimegaController."""
    def __init__(self, for_node: Optional[ParsedHypervisor], mm_command: Optional[str], namespace: str,
                 func_to_call: Optional[str], return_item: bool = False):
        self.for_node: Optional[ParsedHypervisor] = for_node
        self.namespace: str = namespace
        self.mm_command: Optional[str] = mm_command
        self.func_to_call: Optional[str] = func_to_call
        self.return_item = return_item
        self.result: [{}] = None
        self.output: str = ""
        self.exit_code: int = -1
        self.minimega_started: bool = False    # can probably get rid of all of these as well (TLT)
        self.networks_started: bool = False
        self.all_vms_quit: bool = False

    def print_data(self) -> str:
        """Use this method for spilling the contents of an instance."""
        s = "MinimegaItem\n"
        s += f"\t_for_node: {self.for_node}\n"
        s += f"\t_namespace: {self.namespace}\n"
        s += f"\t_command: {self.mm_command}\n"
        s += f"\t_func_to_call: {self.func_to_call}\n"
        s += f"\t_return_item: {self.return_item}\n"
        s += f"\t_result: {self.result}\n"
        s += f"\t_output: {self.output}\n"
        return s


class SnapshotItem:

    def __init__(self, vm_list: List[str], namespace: str):  # for_node: str, ):

        # self.for_node: str = for_node

        self.vm_list: List[str] = vm_list

        self.namespace = namespace

        self.snapshots_complete = False
        self.save_names: List[str] = []
        self.save_time_str: str = ""
        self.output: str = ""
        self.exit_code: int = -1

    def print_data(self) -> str:
        return "NOT DEFINED"


class ResourceCheckItem:

    def __init__(self, for_node: str, files_to_check: List[str]):

        self.for_node: str = for_node

        self.files_to_check: List[str] = files_to_check

        self.unavailable_files_list: List[str] = []

    def print_data(self) -> str:
        return "NOT DEFINED"


class ResourceReleaseItem:

    def __init__(self, nodes: List[str]):

        self.nodes: List[str] = nodes

    def print_data(self) -> str:
        return "NOT DEFINED"


class NetdiscoverItem:

    def __init__(self, for_node: str, netdiscover_args: List[str]):

        self.for_node: str = for_node

        self.arguments_list: List[str] = netdiscover_args

        self.all_scans_complete = 0
        self.output: str = ""
        self.exit_code: int = -1


class SubprocessItem:
    def __init__(self, for_node: str = "undefined", argument_list: List[str] = None,
                 command_str: str = "", action: str = "", context: str = "", shell: bool = False):
        self.for_node: str = for_node
        self.argument_list: List[str] = argument_list
        self.output: str = ""
        self.command_str: str = command_str     # This is anticipated to be used with SockServer/SockClient (TLT).
        self.action: str = action               # Used by socket communications between node and VM.
        self.context: str = context
        self.shell = shell
        self.exit_code: int = -1

    def print_data(self) -> str:
        """Use this method for spilling the contents of an instance."""
        s = "SubprocessItem:\n"
        s += f"\tfor_node: {self.for_node}\n"
        s += f"\targument_list: {self.argument_list}\n"
        s += f"\toutput: {self.output}\n"
        s += f"\tcommand_str: {self.command_str}\n"
        s += f"\taction: {self.action}\n"
        s += f"\tcontext: {self.context}\n"
        s += f"\tshell: {self.shell}\n"
        s += f"\texit_code: {self.exit_code}\n"
        return s


class SSHItem:

    def __init__(self, for_node: str, command: str, host_or_ip: str, username: str, password: str, port: int):

        self.for_node: str = for_node

        self.command: str = command
        self.host_or_ip: str = host_or_ip
        self.username: str = username
        self.password: str = password
        self.port: int = port

        self.output: str = ""
        self.exit_code: int = -1

    def print_data(self) -> str:
        return "NOT DEFINED"


class PowerShellItem:

    def __init__(self, for_node: str, command: str, command_type: str, host_or_ip: str, username: str,
                 password: str, port: int):

        self.for_node: str = for_node

        self.command: str = command
        self.command_type: str = command_type
        self.host_or_ip: str = host_or_ip
        self.username: str = username
        self.password: str = password
        self.port: int = port

        self.output: str = ""
        self.exit_code: int = -1

    def print_data(self) -> str:
        return "NOT DEFINED"


class MeasurementItem:

    def __init__(self, for_node: str, m_type: str = "", target: str = ""):

        self.for_node: str = for_node

        self.m_type: str = m_type
        self.target: str = target

        # for notification from attack controller
        self.success = False
        self.step_id = False

    def print_data(self) -> str:
        return "NOT DEFINED"


class GUIItem:

    def __init__(self, new_stage: int = -1, new_iteration: int = -1, current_iteration = -1, new_message: str = "",
                 clicked: bool = False, clicked_name: str = "", minimum_display_sec: float = 0.0):
        self.new_stage: int = new_stage
        self.new_iteration: int = new_iteration
        self.current_iteration: int = current_iteration
        self.new_message: str = new_message
        self.clicked: bool = clicked
        self.clicked_name: str = clicked_name

        self.minimum_display_sec: float = minimum_display_sec

        self.check_test_type: bool = False
        self.test_type: str = "manual"

        self.minimega_hanging: bool = False

    def print_data(self) -> str:
        """Use this method for spilling the contents of an instance."""
        s = "GUIItem:\n"
        s += f"\tnew_stage: {self.new_stage}\n"
        s += f"\tnew_iteration: {self.new_iteration}\n"
        s += f"\tcurrent_iteration: {self.current_iteration}\n"
        s += f"\tnew_message: {self.new_message}\n"
        s += f"\tclicked: {self.clicked}\n"
        s += f"\tclicked_name: {self.clicked_name}\n"
        s += f"\tminimum_display_sec: {self.minimum_display_sec}\n"
        s += f"\tcheck_test_type: {self.check_test_type}\n"
        s += f"\ttest_type: {self.test_type}\n"
        s += f"\tminimega_hanging: {self.minimega_hanging}\n"
        return s


class DnsmasqItem:
    """Simple class used by minimega controller for deleting stale dnsmasq processes."""
    def __init__(self, node: ParsedHypervisor):
        self.node = node

    def print_data(self) -> str:
        s = "DnsmasqItem:\n"
        s += f"\tnode: {self.node}\n"
        return s


class ControllerRequestItem:
    """Simple class for sending Controller Request items. Such as sending web controller a request item"""
    def __init__(self, function_name: str):
        self.function_name: str = function_name

    def print_data(self):
        s = "ControllerRequestItem:\n"
        s += f"\tfunction_name: {self.function_name}\n"


# base item for queues;
# TO and FROM tell SchedulerUtility where to send item; SU sends item back to FROM if complete
class QueueItem:
    def __init__(self, item: Union[AgentControlItem, StageItem, MinimegaItem, SnapshotItem, ResourceCheckItem,
                                   NetdiscoverItem, SubprocessItem, SSHItem, PowerShellItem, MeasurementItem,
                                   GUIItem, GUIAgentItem, TestbedRequestItem, OutputItem, StatusItem,
                                   IterationRequestItem, ResourceReleaseItem, DnsmasqItem, ControllerRequestItem,
                                   None],
                 to_name: str, from_name: str, to_iteration: int = -1, from_iteration: int = -1,
                 pass_to_q_out: bool = False, pass_to_q_in: bool = False):

        """Every object has a unique ID. Use this for identifying a particular object even if it might have
        been duplicated under the Python hood. I am certain that passing a QueueItem across a multiprocessing
        Queue does a deep copy to a new object (TLT)."""
        self.id = id(self)
        self.item = item
        self.to_name = to_name
        self.to_iteration = to_iteration
        self.from_name = from_name
        self.from_iteration = from_iteration
        self.pass_to_q_in = pass_to_q_in        # Pass on to inner-process q_in queue (TLT)
        self.pass_to_q_out = pass_to_q_out      # Pass on to inner-process q_out queue (TLT)

        self.complete: bool = False
        self.init_time: float = time.time()
        self.completed_time: float = 0.0

    def mark_complete(self):
        self.complete = True
        self.completed_time = time.time()

    def get_elapsed_time(self) -> Optional[float]:
        if self.completed_time != 0.0:
            return self.completed_time - self.init_time
        else:
            return None

    def print_data(self) -> str:
        """Use this method for spilling the contents of an instance."""
        s = "QueueItem:\n"
        s += f"\tid: {self.id}\n"
        s += f"\titem: {self.item}\n"
        s += f"\tto_name: {self.to_name}\n"
        s += f"\tto_iteration: {self.to_iteration}\n"
        s += f"\tfrom_name: {self.from_name}\n"
        s += f"\tfrom_iteration: {self.from_iteration}\n"
        s += f"\tcomplete: {self.complete}\n"
        s += f"\tpass_to_q_in: {self.pass_to_q_in}\n"
        s += f"\tpass_to_q_out: {self.pass_to_q_out}\n"
        s += f"\tinit_time: {self.init_time}\n"
        s += f"\tcompleted_time: {self.completed_time}\n"
        return s
