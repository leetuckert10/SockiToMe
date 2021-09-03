
from copy import deepcopy
from datetime import datetime
from typing import Dict, List, Any, Optional

from static_variables import *


# TODO: update config files for key filename instead of password and then remove password parsing entirely
class ParsedHypervisor:
    def __init__(self, node_alias: str = "", hostname: str = "", max_iterations: int = 1, port: str = "22",
                 username: str = "root", nic_name: str = "", cores: str = "", ram: str = "", disk: str = "",
                 key_file: str = TESTBED_CONTROLLER_KEY_ON_NODE):

        self.node_alias: str = node_alias
        self.hostname: str = hostname
        self.max_iterations = max_iterations
        self.port: int = int(port)
        self.username: str = username

        self.nic_name: str = nic_name

        self._current_allocations = 0

        self.cores: int
        if cores != "":
            self.cores = int(cores)
        else:
            self.cores = 0

        self.ram: int
        if ram != "":
            self.ram = int(ram)
        else:
            self.ram = 0

        self.disk: int
        if disk != "":
            self.disk = int(disk)
        else:
            self.disk = 0

        self.key_file: str = key_file

        self.allocated = False

        self.dict_allocated: Dict[str, int] = {"cpu": 0, "ram": 0, "disk": 0}

        self.hostingSpanningTest = False
        self.hostingSpanningTest = False

    def get_current_allocations(self):
        """Utility for getting the current number of iteration allocations."""
        return self._current_allocations

    def get_string(self) -> str:
        s = "Hypervisor::" + self.hostname + ", " + str(self.port)
        return s

    def get_credentials(self) -> (str, int, str, str):
        return self.hostname, self.port, self.username, self.key_file

    def get_allocated_stats(self) -> Dict[str, int]:
        return self.dict_allocated

    def can_allocate_iteration(self) -> bool:
        """This method checks if the current iterations value is less that the maximum simultaneous
        iterations and returns True or False accordingly. It is called by ResourceController."""
        if self._current_allocations < self.max_iterations:
            self._current_allocations += 1
            return True
        else:
            return False

    def decrement_current_allocations(self):
        self._current_allocations -= 1


class ParsedCyberNode:

    def __init__(self, node_id: str, node_type: str, hostname: str, hardware: str, software: str):

        self.node_id = node_id
        self.node_type = node_type
        self.hostname = hostname
        self.hardware = hardware
        self.software = software

    def get_string(self) -> str:
        s = "CyberNode::" + self.node_id + ", " + self.node_type + ", " + self.hostname
        return s


# encapsulates network details and generates launch commands
class ParsedNetwork:

    # class variable--not instance
    tap_iterator = 0

    def __init__(self, switch_name: str, alias: str, bridge: str, tap_name: Optional[str], tap_ip: str, tap_netmask: str,
                 dhcp_start: str = "", dhcp_end: str = "", config_file: str = ""):

        self.switch_name = switch_name
        self.alias = alias
        self.bridge = bridge
        self.tap_name = tap_name
        self.tap_ip = tap_ip
        self.tap_netmask = tap_netmask

        self.dhcp_start: str
        if dhcp_start is None:
            self.dhcp_start = ""
        else:
            self.dhcp_start = dhcp_start

        self.dhcp_end: str
        if dhcp_end is None:
            self.dhcp_end = ""
        else:
            self.dhcp_end = dhcp_end

        self.config_file: str
        if config_file is None:
            self.config_file = ""
        else:
            self.config_file = config_file

        # TODO: get interface name when network is brought up in agent instead of assuming
        # NOTE: this assumes that networks are parsed and brought up sequentially on a 'fresh' minimega execution
        # and that resets don't trip it up
        self.interface_name = self.tap_name
        ParsedNetwork.tap_iterator += 1

    def get_string(self) -> str:
        s = "Network::" + self.alias + ", " + self.bridge + " ," + self.tap_ip + ", " + self.tap_netmask

        if self.tap_name is not None:
            s = s + ", " + self.tap_name

        return s

    def get_bridge(self, iter) -> str:
        return self.bridge.replace(TAG_ITERATION, str(iter))

    def get_iface(self, iter) -> str:
        return self.interface_name.replace(TAG_ITERATION, str(iter))

    def get_mm_commands(self, iter: int, b_ctl: bool=False, octet3="", octet4="") -> List[str]:
        commands = []
        # b_ctl: bool = STR_CONTROL_INTERFACE in self.alias

        # NOTE: no need to specify namespace because the iteration controller
        # will be using a minimega connection object which is namespace specific
        t = "tap create " + self.alias + " bridge " + self.bridge.replace(TAG_ITERATION, str(iter)) +\
            " ip " + self.tap_ip + "/" + self.tap_netmask

        if self.tap_name is not None:
            t = t + " " + self.tap_name.replace(TAG_ITERATION, str(iter))

        if b_ctl:
            t = t.replace(TAG_OCTET_3, octet3)
            t = t.replace(TAG_BASE_PLUS1, octet4)

        commands.append(t)

        if (not self.dhcp_start == "") and (not self.dhcp_end == ""):
            d = "dnsmasq start " + self.tap_ip + " " + self.dhcp_start + " " + self.dhcp_end

            if b_ctl:
                d = d.replace(TAG_OCTET_3, octet3)
                d = d.replace(TAG_BASE_PLUS1, octet4)
                d = d.replace(TAG_BASE_PLUS2, str(int(octet4)+1))

            if (self.config_file is not None) and (self.config_file != ""):
                d += " " + self.config_file
            commands.append(d)
            
        return commands


# encapsulates virtual machine details and generates launch commands
class ParsedVirtualMachine:
    def __init__(self, name: str, cpu_arch: str, cpus: int, memory: int, disk: str, cdroms: List[str], nets: List[str],
                 operating_system: str="", drive_snapshot: str="true", analyze: bool = False,
                 state_snapshot: str="", mm_passthrough: Dict[str, Any]=None):

        self.name = name
        self.cpu_arch = cpu_arch
        self.cpus = cpus
        self.memory = memory
        self.disk = disk
        self.cdroms = cdroms
        self.nets = nets
        self.drive_snapshot = drive_snapshot
        self.analyze = analyze
        self.state_snapshot = state_snapshot
        self.operating_system = operating_system

        # mm_passthrough contains a dict of str -> str or str -> List[str], depending on key
        self.mm_passthrough = deepcopy(mm_passthrough)

        """ip_address should be set by parser if static or detection from minimega/netdiscover."""
        self.ip_address = ""

        self.mac_net_ip: (str, str, str) = []

        for n in self.nets:
            try:
                c_split = n.split(",")
                mac = c_split[2]
                net_alias = c_split[1]

                tup = (mac, net_alias, "")

                self.mac_net_ip.append(tup)

                # for i in range(len(self.mac_net_ip)):
                #     (mac_a, alias, ip) = self.mac_net_ip[i]
                #     if mac == mac_a:
                #         new_tup = (mac, alias, "")
                #         self.mac_net_ip[i] = new_tup

                # for tup in self.mac_net_ip:
                #     (mac_a, alias, ip) = tup
                #     if mac == mac_a:
                #         new_tup = (mac, alias, "")
                #         self.mac_net_ip.
                # self.mac_net_ip[mac] = (net_alias, "")

            except:
                raise Exception(f"ERROR: could not parse alias and mac from net: {n}!")

    def get_string(self) -> str:

        s = "VirtualMachine::" + self.name + ", " + self.cpu_arch + ", [ "
        for n in self.nets:
            s += n + " "
        s += "]"
        return s

    # return filenames of resources needed to launch VM
    def get_resources(self) -> List[str]:

        # all VMs should have at least disk
        resources = [self.disk]

        if self.state_snapshot != "":
            resources.append(self.state_snapshot)

        for cd in self.cdroms:
            resources.append(cd)

        if 'mm-kernel' in self.mm_passthrough:
            resources.append(self.mm_passthrough['mm-kernel'])

        if 'mm-initrd' in self.mm_passthrough:
            resources.append(self.mm_passthrough['mm-initrd'])

        return resources

    def get_mm_commands(self) -> List[str]:

        # NOTE: keep these in order or spend a few more hours debugging ARM launches

        commands = []

        # clear
        c = "clear vm config"
        commands.append(c)

        # drive_snapshot
        if self.drive_snapshot in TRUE_VALUES:    # read as str from file, not bool
            c = "vm config snapshot true"
            commands.append(c)
        else:
            c = "vm config snapshot false"
            commands.append(c)

        # arm
        if self.cpu_arch == "aarch64":

            # turn off backchannel functionality
            c = "vm config backchannel false"
            commands.append(c)

            # explicitly set binary path
            c = "vm config qemu " + QEMU_AARCH64_PATH
            commands.append(c)

            # specify type
            c = "vm config machine virt"
            commands.append(c)

            # memory
            c = "vm config memory " + str(self.memory)
            commands.append(c)

            # specify proc
            c = "vm config cpu cortex-a53"
            commands.append(c)

            # nets
            c = "vm config net "
            for n in self.nets:
                c += n + " "
            c = c.strip()
            commands.append(c)

            # specify drive root for Linux kernel
            c = "vm config append \"root=/dev/vda2\""
            commands.append(c)

            # remove graphics
            c = "vm config qemu-override \"-vga std\" \" \""
            commands.append(c)

            # # remove usb
            # c = "vm config qemu-override \"-usb -device usb-ehci,id=ehci\" \" \""
            # commands.append(c)

            # remove input device
            c = "vm config qemu-override \"-device usb-tablet,bus=usb-bus.0\" \" \""
            commands.append(c)

            # remove cdrom
            c = "vm config qemu-override \"-drive media=cdrom\" \" \""
            commands.append(c)

            # remove 'none' net if added during changes
            c = "vm config qemu-override \"-net none\" \" \""
            commands.append(c)

            # specify arm-compatible driver
            c = "vm config qemu-override \"-device driver=e1000\" \"-device virtio-net-device\""
            commands.append(c)

            # remove incompatible addressing
            c = "vm config qemu-override \",bus=pci.1,addr=0x1\" \" \""
            commands.append(c)

            c = "vm config qemu-override \",bus=pci.1,addr=0x2\" \" \""
            commands.append(c)

            c = "vm config qemu-override \",bus=pci.1,addr=0x3\" \" \""
            commands.append(c)

            if self.drive_snapshot in TRUE_VALUES:  # read as str from file, not bool
                c = "vm config qemu-override \",if=ide,cache=unsafe\" \",cache=unsafe\""
                commands.append(c)

            else:
                c = "vm config qemu-override \",if=ide,cache=writeback\" \",cache=writeback\""
                commands.append(c)

        else:   # x86

            # explicitly set binary path
            c = "vm config qemu " + QEMU_X86_64_PATH
            commands.append(c)

            # specify drive root for Linux kernel
            c = "vm config qemu-append -enable-kvm"
            commands.append(c)

            # cpus
            c = "vm config vcpu " + str(self.cpus)
            commands.append(c)

            # memory
            c = "vm config memory " + str(self.memory)
            commands.append(c)

            # nets
            c = "vm config net "
            for n in self.nets:
                c += n + " "
            c = c.strip()
            commands.append(c)

            # cdroms
            if self.cdroms:  # cdroms list is not empty

                if len(self.cdroms) == 1:
                    c = "vm config cdrom " + self.cdroms[0]
                    commands.append(c)

                elif len(self.cdroms) == 2:

                    # shenanigans for two cdrom drives
                    c = "vm config qemu-override \" media=cdrom \" \" file=" + self.cdroms[1] + ",index=1,media=cdrom \""
                    commands.append(c)

                    c = "vm config qemu-append -drive file=" + self.cdroms[0] + ",index=0,media=cdrom -enable-kvm"
                    commands.append(c)

                    c = "vm config qemu-override \"media=disk\" \"media=disk,index=2\""
                    commands.append(c)

            # NOTE: -vga std (mm default) seems to be breaking some ubuntu 18.04 graphics
            c = "vm config vga virtio"
            commands.append(c)

        # check if key is in dict and add single or multiple commands
        if 'mm-append' in self.mm_passthrough:
            for a in self.mm_passthrough['mm-append']:
                c = "vm config append " + a
                commands.append(c)

        if 'mm-qemu-append' in self.mm_passthrough:
            for q in self.mm_passthrough['mm-qemu-append']:
                c = "vm config qemu-append " + q
                commands.append(c)

        if 'mm-qemu-override' in self.mm_passthrough:
            for o in self.mm_passthrough['mm-qemu-override']:
                c = "vm config qemu-override " + o
                commands.append(c)

        # disk
        c = "vm config disk " + self.disk
        commands.append(c)

        if 'mm-kernel' in self.mm_passthrough:
            c = "vm config kernel " + self.mm_passthrough['mm-kernel']
            commands.append(c)

        if 'mm-initrd' in self.mm_passthrough:
            c = "vm config initrd " + self.mm_passthrough['mm-initrd']
            commands.append(c)

        # state_snapshot
        if self.state_snapshot is not "":
            c = "vm config migrate " + self.state_snapshot
            commands.append(c)

        # launch + name
        c = "vm launch kvm " + self.name
        commands.append(c)

        # moved to iteration controller
        # start
        # c = "vm start " + self.name
        # commands.append(c)

        return commands

    def reset_ip_addresses(self) -> None:
        self.ip_address = ""

        for i in range(len(self.mac_net_ip)):
            (mac, net, ip) = self.mac_net_ip[i]
            new_tup = (mac, net, "")
            self.mac_net_ip[i] = new_tup
            # (alias, ip) = self.mac_net_ip[mac]
            # self.mac_net_ip[mac] = (alias, "")

    def set_ip_address(self, ip: str) -> None:
        self.ip_address = ip

    def get_ip_address(self) -> Optional[str]:

        # return main/management if available but try to return any other if possible
        if (self.ip_address is not None) and (self.ip_address != ""):
            return self.ip_address

        else:
            return self.get_any_ip_address()

    def get_any_ip_address(self) -> Optional[str]:

        # for mac in self.mac_net_ip:
        #     (alias, ip) = self.mac_net_ip[mac]
        #
        #     if (ip is not None) and (ip != ""):
        #         return ip

        reverse_list = self.mac_net_ip[::-1]    # looking for IP in reverse order to solve interface disappearance bug

        """This print statement was causing an a acquire_lock dead lock. Why? Is it because logging is writing
        both to the screen and to a file and the conflict was writing to the screen? TLT does not know..."""
        # print(f"Reverse list: {reverse_list}")

        for i in range(len(reverse_list)):
            # print(f"Reverse network {i} = {reverse_list[i]}")
            (mac, net, ip) = reverse_list[i]

            if (ip is not None) and (ip != "") and "10.254" not in ip:
                return ip

        return None

    def get_ip_address_on_net(self, net_alias: str) -> Optional[str]:

        for (mac, net, ip) in self.mac_net_ip:
            if net == net_alias:
                return ip

        # for mac in self.mac_net_ip:
        #     (alias, ip) = self.mac_net_ip[mac]
        #     if alias == net_alias:
        #         return ip

        return None

    def set_ip_address_for_mac(self, ip_address: str, mac_address: str) -> str:
        for i in range(len(self.mac_net_ip)):
            (mac, net, ip) = self.mac_net_ip[i]
            if mac == mac_address:
                new_tup = (mac, net, ip_address)
                self.mac_net_ip[i] = new_tup
                return "Success"
            else:
                continue
        return f"ERROR: Could not load tuple for mac: {mac_address}"

    def has_an_ip_address(self) -> bool:
        has_one = False

        for (mac, net, ip) in self.mac_net_ip:
            if (ip is not None) and (ip != ""):
                has_one = True
                break

        # for mac in self.mac_net_ip:
        #     (alias, ip) = self.mac_net_ip[mac]
        #     if (ip is not None) and (ip != ""):
        #         has_one = True

        return has_one

    def has_a_management_ip_address(self) -> bool:

        if (self.ip_address is not None) and (self.ip_address != ""):
            return True
        else:
            return False


# encapsulates details needed for 'ssh', 'cmd', or 'powershell' commands; RPCAgent interprets and executes shells
class ParsedRemoteShell:

    def __init__(self, mm_vm_name: str, hostname_or_ip: str, port: str, username: str, password: str, shell_type: str):

        self.mm_vm_name = mm_vm_name
        self.hostname_or_ip = hostname_or_ip
        self.port = port
        self.username = username
        self.password = password
        self.type = shell_type  # ssh, cmd, or powershell

    def get_string(self) -> str:
        s = "RemoteShell::" + self.type + ", " + self.hostname_or_ip + ", " + self.port
        return s


class ParsedGUIAction:

    def __init__(self, action_id: str, source_name: str, target_name: str, gui_type: str, script: str, run_before: str,
                 run_after: str, automated: bool, manual: bool):

        self.id: str = action_id
        self.source_name: str = source_name
        self.target_name: str = target_name
        self.gui_type: str = gui_type
        self.script: str = script
        self.run_before: str = run_before
        self.run_after: str = run_after
        self.automated: bool = automated
        self.manual: bool = manual

        if (self.script is not None) and ('&amp;' in self.script):
            self.script = self.script.replace('&amp;', '&')

    def update_source_ip(self, ip_address: str):
        if TAG_SOURCE_IP in self.script:
            self.script = self.script.replace(TAG_SOURCE_IP, ip_address)

    def update_target_ip(self, ip_address: str):
        if TAG_TARGET_IP in self.script:
            self.script = self.script.replace(TAG_TARGET_IP, ip_address)

    def update_iteration(self, iteration: int):
        if TAG_ITERATION in self.script:
            self.script = self.script.replace(TAG_ITERATION, str(iteration))

    def update_user(self, user: str):
        if TAG_USER in self.script:
            self.script = self.script.replace(TAG_USER, user)

    def update_hostname(self, hostname: str):
        if TAG_HOSTNAME in self.script:
            self.script = self.script.replace(TAG_HOSTNAME, hostname)

    def get_string(self) -> str:
        s = "GUIAction::" + self.id + ", " + self.source_name + ", [" + self.script + "]"
        return s


class ParsedStageLimit:

    def __init__(self, stage_id: int, limit: int):
        self.id: int = stage_id
        self.limit: int = limit

    def get_string(self) -> str:
        s = "ParsedStageLimit::" + str(self.id) + ", " + str(self.limit)
        return s


class ParsedAction:

    def __init__(self, action_id: str, source_name: str, target_name: str, action_type: str, script: str,
                 execution: str, stage: str, controller: str, start_delay: str, end_delay: str, run_before: str,
                 run_after: str, timeout: int, shell: bool, automated: bool, manual: bool):

        self.id: str = action_id
        self.source_name: str = source_name
        self.target_name: str = target_name
        self.type: str = action_type
        self.script: str = script
        self.execution: str = execution    # TODO: unused
        self.stage: int = int(stage)
        self.controller: str = controller
        self.start_delay: float = float(start_delay)
        self.end_delay: float = float(end_delay)
        self.run_before: str = run_before
        self.run_after: str = run_after
        self.timeout: int = timeout
        self.shell = shell
        self.automated: bool = automated
        self.manual: bool = manual

        if (self.script is not None) and ('&amp;' in self.script):
            self.script = self.script.replace('&amp;', '&')

    def get_string(self) -> str:
        s = "Action::" + self.id + ", " + self.type + ", " + str(self.stage)
        return s

    def print_action(self) -> str:
        s: str = "Action Definition:\n"
        s += f"\t         Id: {self.id}\n"
        s += f"\tSource Name: {self.source_name}\n"
        s += f"\tTarget Name: {self.target_name}\n"
        s += f"\t       Type: {self.type}\n"
        s += f"\t     Script: {self.script}\n"
        s += f"\t      Stage: {self.stage}\n"
        s += f"\t Controller: {self.controller}\n"
        s += f"\tStart Delay: {self.start_delay}\n"
        s += f"\t  End Delay: {self.end_delay}\n"
        s += f"\t Run Before: {self.run_before}\n"
        s += f"\t  Run After: {self.run_after}\n"
        s += f"\t    Timeout: {self.timeout}\n"
        s += f"\t      Shell: {self.shell}\n"
        s += f"\t  Automated: {self.automated}\n"
        s += f"\t     Manual: {self.manual}"
        return s


    def update_source_ip(self, ip_address: str):
        if TAG_SOURCE_IP in self.script:
            self.script = self.script.replace(TAG_SOURCE_IP, ip_address)

    def update_target_ip(self, ip_address: str):
        if TAG_TARGET_IP in self.script:
            self.script = self.script.replace(TAG_TARGET_IP, ip_address)

    def update_iteration(self, iteration: int):
        if TAG_ITERATION in self.script:
            self.script = self.script.replace(TAG_ITERATION, str(iteration))

    def update_user(self, user: str):
        if TAG_USER in self.script:
            self.script = self.script.replace(TAG_USER, user)

    def update_hostname(self, hostname: str):
        if TAG_HOSTNAME in self.script:
            self.script = self.script.replace(TAG_HOSTNAME, hostname)

    def update_src_tap(self, tap: str):
        if TAG_SRC_TAP in self.script:
            self.script = self.script.replace(TAG_SRC_TAP, tap)

    def update_dst_tap(self, tap: str):
        if TAG_DST_TAP in self.script:
            self.script = self.script.replace(TAG_DST_TAP, tap)


class ParsedAttackStep:

    def __init__(self, step_id: str, source_name: str, target_name: str, action_type: str, script: str,
                 start_delay: str, end_delay: str, success_function: str, success_parameter: str,
                 success_str: str, failure_str: str, shell: bool, automated: bool, manual: bool):

        self.step_id: str = step_id
        self.source_name: str = source_name
        self.target_name: str = target_name
        self.type: str = action_type
        self.script: str = script
        self.start_delay: float = float(start_delay)
        self.end_delay: float = float(end_delay)
        self.success_function: str = success_function
        self.success_parameter: str = success_parameter
        self.success_str: str = success_str
        self.failure_str: str = failure_str
        self.shell = shell
        self.automated: bool = automated
        self.manual: bool = manual

        self.success_step = None
        self.failure_step = None

        if (self.script is not None) and ('&amp;' in self.script):
            self.script = self.script.replace('&amp;', '&')

    def update_source_ip(self, ip_address: str):
        if TAG_SOURCE_IP in self.script:
            self.script = self.script.replace(TAG_SOURCE_IP, ip_address)

    def update_target_ip(self, ip_address: str):
        if TAG_TARGET_IP in self.script:
            self.script = self.script.replace(TAG_TARGET_IP, ip_address)

    def get_string(self) -> str:
        s = f"{self.step_id} {self.source_name} {self.type}"
        return s


class ParsedMeasurementAction:
    def __init__(self, action_id: str, source_name: str, target_name: str, type: str, script: str, iteration: int,
                 start_delay: str, end_delay: str, run_before: str, run_after: str, timeout: int,
                 automated: bool, shell: bool,
                 manual: bool, measurement_type: str):

        self.id: str = action_id
        self.source_name: str = source_name
        self.target_name: str = target_name
        self.type: str = type
        self.script: str = script
        self.iteration: int = iteration
        self.start_delay: float = float(start_delay)
        self.end_delay: float = float(end_delay)
        self.run_before: str = run_before
        self.run_after: str = run_after
        self.timeout: int = timeout
        self.automated: bool = automated
        self.shell = shell
        self.manual: bool = manual
        self.measurement_type: str = measurement_type

        if (self.script is not None) and ('&amp;' in self.script):
            self.script = self.script.replace('&amp;', '&')

    def update_source_ip(self, ip_address: str):
        if TAG_SOURCE_IP in self.script:
            self.script = self.script.replace(TAG_SOURCE_IP, ip_address)

    def update_target_ip(self, ip_address: str):
        if TAG_TARGET_IP in self.script:
            self.script = self.script.replace(TAG_TARGET_IP, ip_address)

    def update_iteration(self, iteration: int):
        if TAG_ITERATION in self.script:
            self.script = self.script.replace(TAG_ITERATION, str(iteration))

    def update_user(self, user: str):
        if TAG_USER in self.script:
            self.script = self.script.replace(TAG_USER, user)

    def update_hostname(self, hostname: str):
        if TAG_HOSTNAME in self.script:
            self.script = self.script.replace(TAG_HOSTNAME, hostname)

    def update_src_tap(self, tap: str):
        if TAG_SRC_TAP in self.script:
            self.script = self.script.replace(TAG_SRC_TAP, tap)

    def update_dst_tap(self, tap: str):
        if TAG_DST_TAP in self.script:
            self.script = self.script.replace(TAG_DST_TAP, tap)

    def get_string(self) -> str:
        s = f"Type = {self.measurement_type}; Description = {self.id}"
        return s


class ParsedMeasurement:
    def __init__(self, measurement_type: str, source_name: str, target_name: str, attributes: Dict = None):

        self.type = measurement_type

        self.source_name: str
        if source_name is None:
            self.source_name = ""
        else:
            self.source_name = source_name

        self.target_name: str
        if target_name is None:
            self.target_name = ""
        else:
            self.target_name = target_name

        self.attributes: Dict
        if attributes is None:
            self.attributes = {}
        else:
            self.attributes = deepcopy(attributes)

    def get_string(self) -> str:
        s = "Measurement::" + self.type + ", " + self.source_name + ", " + self.target_name + ", " + str(self.attributes)
        return s
