import sublime
from sublime import Window
from sublime_plugin import TextCommand
from sublime_plugin import EventListener
from threading import Thread
import json
import sys
from subprocess import Popen, PIPE
from time import sleep
from .WebSocket.WebSocketServer import WebSocketServer
from .WebSocket.AbstractOnClose import AbstractOnClose
from .WebSocket.AbstractOnMessage import AbstractOnMessage
from .Http.HttpServer import HttpServer
from .Http.AbstractOnRequest import AbstractOnRequest
from .Http.Request import Request
from .Http.Response import Response


server = None


class BrowserReplGlobals():
    """
    'Namespace' for global vars.
    """
    http_status_server_thread = None


def plugin_loaded():
    print('BrowserRepl starting …')
    settings = sublime.load_settings('BrowserRepl.sublime-settings')
    BrowserReplGlobals.http_status_server_thread = HttpStatusServerThread(settings)
    BrowserReplGlobals.http_status_server_thread.start()

    # Utils.replace_connected_with_disconnected_prefix()


def plugin_unloaded():
    print('BrowserRepl stopping…')
    print(BrowserReplGlobals.http_status_server_thread)
    if BrowserReplGlobals.http_status_server_thread is None:
        return

    BrowserReplGlobals.http_status_server_thread.stop()


##     ## ######## ######## ########      ######  ######## ########  ##     ## ######## ########  
##     ##    ##       ##    ##     ##    ##    ## ##       ##     ## ##     ## ##       ##     ## 
##     ##    ##       ##    ##     ##    ##       ##       ##     ## ##     ## ##       ##     ## 
#########    ##       ##    ########      ######  ######   ########  ##     ## ######   ########  
##     ##    ##       ##    ##                 ## ##       ##   ##    ##   ##  ##       ##   ##   
##     ##    ##       ##    ##           ##    ## ##       ##    ##    ## ##   ##       ##    ##  
##     ##    ##       ##    ##            ######  ######## ##     ##    ###    ######## ##     ## 

class HttpStatusServerThread(Thread):
    def __init__(self, settings):
        print('HttpStatusServerThread __init__')
        super().__init__()
        server_port = int(settings.get('server_port', 4002))
        self._server = HttpServer('localhost', server_port)
        self._server.on_request(OnRequest(settings))

    def run(self):
        try:
            self._server.start()
        except OSError as e:
            Utils.show_error(e, 'HttpStatusServerThread')
            raise e

    def stop(self):
        self._server.stop()

class OnRequest(AbstractOnRequest):
    def __init__(self, settings):
        # self.new_window_on_connect = bool(settings.get('new_window_on_connect', False))
        # self.window_command_on_connect = str(settings.get('window_command_on_connect', 'focus_sublime_window'))
        self._settings = settings

    def on_request(self, request):
        print('on_request')
        # if len(sublime.windows()) == 0 or self.new_window_on_connect:
        #     sublime.run_command('new_window')

        # if len(self.window_command_on_connect) > 0:
        #     sublime.active_window().run_command(self.window_command_on_connect)

        web_socket_server_thread = WebSocketServerThread(self._settings)
        web_socket_server_thread.start()
        while not web_socket_server_thread.get_server().get_running():
            sleep(0.1)

        port = web_socket_server_thread.get_server().get_port()
        Utils.show_status('Connection opened')

        print('return Resonse')
        return Response(json.dumps({"WebSocketPort": port, "ProtocolVersion": 1}),
                        "200 OK",
                        {'Content-Type': 'application/json'})




# class ReplaceContentCommand(TextCommand):
#     """
#     Replaces the views complete text content.
#     """
#     def run(self, edit, **args):
#         self.view.replace(edit, sublime.Region(0, self.view.size()), args['text'])
#         text_length = len(args['text'])
#         self.view.sel().clear()

#         if 'selections' in args and len(args['selections']) > 0:
#             selection = args['selections'][0]
#             self.view.sel().add(sublime.Region(selection['start'], selection['end']))
#         else:
#             self.view.sel().add(sublime.Region(text_length, text_length))





##      ##  ######      ######  ######## ########  ##     ## ######## ########  
##  ##  ## ##    ##    ##    ## ##       ##     ## ##     ## ##       ##     ## 
##  ##  ## ##          ##       ##       ##     ## ##     ## ##       ##     ## 
##  ##  ##  ######      ######  ######   ########  ##     ## ######   ########  
##  ##  ##       ##          ## ##       ##   ##    ##   ##  ##       ##   ##   
##  ##  ## ##    ##    ##    ## ##       ##    ##    ## ##   ##       ##    ##  
 ###  ###   ######      ######  ######## ##     ##    ###    ######## ##     ## 

class WebSocketServerThread(Thread):
    def __init__(self, settings):
        super().__init__()
        print('start websockerserver')
        self._server = WebSocketServer('localhost', 0)
        self._server.on_message(OnConnect(settings))
        self._server.on_close(OnClose(settings))
        global server
        server = self._server



    def run(self):
        self._server.start()

    def get_server(self):
        return self._server

class OnConnect(AbstractOnMessage):
    def __init__(self, settings):
        self._settings = settings

    def on_message(self, text):
        print('OnConnect - on_message')
        try:
            # request = json.loads(text)
            # window_helper = WindowHelper()
            # current_view = window_helper.add_file(request['title'], request['text'])
            # OnSelectionModifiedListener.bind_view(current_view, self._web_socket_server)
            # self._web_socket_server.on_message(OnMessage(self._settings, current_view))
            # current_view.window().focus_view(current_view)
            # Utils.set_syntax_by_host(request['url'], current_view)

            global server
            server = self._web_socket_server

            self._web_socket_server.send_message(response)
        except ValueError as e:
            Utils.show_error(e, 'Invalid JSON')

# TODO: maybe we don't really need this one
class OnMessage(AbstractOnMessage):
    def __init__(self, settings, current_view):
        self._current_view = current_view
        self._settings = settings

    def on_message(self, text):
        print('on_message')
        # try:
        #     # request = json.loads(text)
        #     # self._current_view.run_command('replace_content', request)
        #     # self._current_view.window().focus_view(self._current_view)
        # except ValueError as e:
        #     Utils.show_error(e, 'Invalid JSON')


class OnClose(AbstractOnClose):
    def __init__(self, settings):
        self._settings = settings
        # self._close_view_on_disconnect = bool(settings.get('close_view_on_disconnect', False))

    def on_close(self):
        # view_id = OnSelectionModifiedListener.find_view_id_by_web_socket_server_id(self._web_socket_server)
        # if view_id is not None:
        #     view = Utils.find_view_by_id(view_id)
        #     if view is not None:
        #         Utils.mark_view_as(view, 'disconnected')

        # if self._close_view_on_disconnect:
        #     Utils.close_view_by_id(view_id)

        # OnSelectionModifiedListener.unbind_view_by_web_socket_server_id(self._web_socket_server)
        Utils.show_status('Connection closed')




##     ## ######## #### ##        ######  
##     ##    ##     ##  ##       ##    ## 
##     ##    ##     ##  ##       ##       
##     ##    ##     ##  ##        ######  
##     ##    ##     ##  ##             ## 
##     ##    ##     ##  ##       ##    ## 
 #######     ##    #### ########  ######  

def run(cmd, args = [], source="", cwd = None, env = None):
    if not type(args) is list:
        args = [args]
    if sys.platform == "win32":
        proc = Popen([cmd]+args, env=env, cwd=cwd, stdout=PIPE, stdin=PIPE, stderr=PIPE, shell=True)
        stat = proc.communicate(input=source)
    else:
        if env is None:
            env = {"PATH": '/usr/local/bin'}
            # env = {"PATH": settings.get('binDir', '/usr/local/bin')}
        if source == "":
            command = [cmd]+args
        else:
            command = [cmd]+args+[source]
        print("cmd:")
        print(command)
        proc = Popen(command, env=env, cwd=cwd, stdout=PIPE, stderr=PIPE)
        stat = proc.communicate()
    okay = proc.returncode == 0
    print("stat:")
    print(stat)
    return {"okay": okay, "out": stat[0], "err": stat[1]}

def brew(args, source):
    if sys.platform == "win32":
        args.append("-s")
    else:
        args.append("-e")
    args.append("-p")
    return run("coffee", args=args, source=source)


def coffeeToJs(coffee):
    args = ['-b']
    res = brew(args, coffee)
    return str(res["out"], "utf-8")




######## ######## ##     ## ########     ######   #######  ##     ## ##     ##    ###    ##    ## ########   ######  
   ##    ##        ##   ##     ##       ##    ## ##     ## ###   ### ###   ###   ## ##   ###   ## ##     ## ##    ## 
   ##    ##         ## ##      ##       ##       ##     ## #### #### #### ####  ##   ##  ####  ## ##     ## ##       
   ##    ######      ###       ##       ##       ##     ## ## ### ## ## ### ## ##     ## ## ## ## ##     ##  ######  
   ##    ##         ## ##      ##       ##       ##     ## ##     ## ##     ## ######### ##  #### ##     ##       ## 
   ##    ##        ##   ##     ##       ##    ## ##     ## ##     ## ##     ## ##     ## ##   ### ##     ## ##    ## 
   ##    ######## ##     ##    ##        ######   #######  ##     ## ##     ## ##     ## ##    ## ########   ######  

class BrowserReplEvalCommand(TextCommand):
    def run(self, edit):
        for region in self.view.sel():
            code = self.view.substr(region)

            # Only interested in empty regions, otherwise they may span multiple  
            # lines, which doesn't make sense for this command.  
            if region.empty():  
                # Expand the region to the full line it resides on, excluding the newline  
                line = self.view.line(region)  
                # Extract the string for the line, and add a newline  
                code = self.view.substr(line)

                if code.endswith('.'):
                    code = code[:-1]

            filename = self.view.file_name().split('/')[-1]
            if filename.endswith('.coffee'):
                js = coffeeToJs(code)
            else:
                js = code

            response = json.dumps({
                'command': 'eval',
                'data':  js
            })

            global server
            server.send_message(response)

class BrowserReplEvalBlockCommand(TextCommand):
    def run(self, edit):
        for region in self.view.sel():

            # Only interested in empty regions, otherwise they may span multiple  
            # lines, which doesn't make sense for this command.  
            if not region.empty():
                return

            # Expand the region to the full line it resides on, excluding the newline  
            line = self.view.line(region)  

            cur_pt = region.b

            self.view.find
            print('region.end:')
            print(region.end())
            print('rg:')
            start = 0
            end = self.view.size()

            next_newline = self.view.find("\n\s*\n", cur_pt)
            if next_newline.a != -1:
                end = next_newline.a
            print('start:')
            print(start)
            print('end:')
            print(end)
            # if rb.a == -1:

            # couldn't find "find previous" command
            all_newlines = self.view.find_all("\n[\s]*\n")
            for rg in all_newlines:
                if rg.b <= cur_pt:
                    start = rg.b

            newRegion = sublime.Region(start, end)

            print('newRegion:')
            print(self.view.substr(newRegion))
            print('----')

            code = self.view.substr(newRegion)

            filename = self.view.file_name().split('/')[-1]
            if filename.endswith('.coffee'):
                js = coffeeToJs(code)
            else:
                js = code

            response = json.dumps({
                'command': 'eval',
                'data':  js
            })

            global server
            server.send_message(response)

class BrowserReplEvalFromSpaceCommand(TextCommand):
    def run(self, edit):
        print('space')
        for region in self.view.sel():

            # Only interested in empty regions, otherwise they may span multiple  
            # lines, which doesn't make sense for this command.  
            if not region.empty():
                return

            cur_pt = region.b
            start = 0
            end = region.b

            # couldn't find "find previous" command
            all_newlines = self.view.find_all("[\t|\s]+")
            for rg in all_newlines:
                if rg.b < cur_pt:
                    start = rg.b


            newRegion = sublime.Region(start, end)

            code = self.view.substr(newRegion)

            if code.endswith('.'):
                code = code[:-1]

            filename = self.view.file_name().split('/')[-1]
            if filename.endswith('.coffee'):
                js = coffeeToJs(code)
            else:
                js = code

            response = json.dumps({
                'command': 'eval',
                'data':  js
            })

            global server
            server.send_message(response)


class BrowserReplEvalUnderCursorCommand(TextCommand):
    def run(self, edit):
        for region in self.view.sel():

            # Only interested in empty regions, otherwise they may span multiple  
            # lines, which doesn't make sense for this command.  
            if not region.empty():
                return

            cur_pt = region.b
            start = 0

            next_newline = self.view.find("\n{1}", region.b)
            end = next_newline.a
            print("next_newline")
            print(next_newline)

            print('0end:')
            print(end)
            # couldn't find "find previous" command
            all_newlines = self.view.find_all("[\t|\s]+")
            for rg in all_newlines:
                if rg.b < cur_pt:
                    start = rg.b

            print('start')
            print(start)

            newRegion = sublime.Region(start, end)

            print('newRegion:')
            print(self.view.substr(newRegion))
            print('----')

            code = self.view.substr(newRegion)

            if code.endswith('.'):
                code = code[:-1]

            filename = self.view.file_name().split('/')[-1]
            if filename.endswith('.coffee'):
                js = coffeeToJs(code)
            else:
                js = code

            response = json.dumps({
                'command': 'eval',
                'data':  js
            })

            global server
            server.send_message(response)

class BrowserReplEvalAutoCompleteCommand(TextCommand):
    def run(self, edit):
        for region in self.view.sel():

            # Only interested in empty regions, otherwise they may span multiple  
            # lines, which doesn't make sense for this command.  
            if not region.empty():
                return

            cur_pt = region.b
            start = 0

            next_newline = self.view.find("\n{1}", region.b)
            end = next_newline.a
            print("next_newline")
            print(next_newline)

            print('0end:')
            print(end)
            # couldn't find "find previous" command
            all_newlines = self.view.find_all("[\t|\s]+")
            for rg in all_newlines:
                if rg.b < cur_pt:
                    start = rg.b

            print('start')
            print(start)

            newRegion = sublime.Region(start, end)

            print('newRegion:')
            print(self.view.substr(newRegion))
            print('----')

            code = self.view.substr(newRegion)

            js = code + ';' #simplification for now

            # filename = self.view.file_name().split('/')[-1]
            # if filename.endswith('.coffee'):
            #     if code.endswith('.'):
            #         code = code[:-1]
            #         js = coffeeToJs(code)
            #         js += '.'
            #     else:
            #         js = coffeeToJs(code)
            # else:
            #     js = code

            response = json.dumps({
                'command': 'auto_complete',
                'data':  js
            })

            global server
            server.send_message(response)






