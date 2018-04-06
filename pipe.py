
import os
import threading

class PipeTX(object):
	def __init__(self, filename):
		self.filename = filename
		try:
			os.mkfifo(filename)
		except Exception as ex:
			print(ex)
	
	def _write_pipe(self, data):
		#Write pipe blocking
		with open(self.filename, "w") as fifo:
			fifo.write(data) #Will be locked here until Pipe is read

	def write(self, data):
		#Write pipe without blocking (creating a thread)
		thread = threading.Thread(
			target=self._write_pipe,
			args=(data,),
			daemon=True
		)
		thread.start()
	


class PipeRX(object):
	def __init__(self, filename):
		self.filename = filename

	def _read_pipe(self):
		with open(self.filename, "r") as pipe:
			return pipe.read() #If no data in pipe, will be locked here until Pipe is written again

	def _read_pipe_event(self, event, stopEvent):
		#Set an Event when Pipe received any data. Ignore data content
		while not stopEvent.isSet():
			if self._read_pipe():
				event.set()

	def create_read_pipe_event(self):
		class _PipeEvent(object):
			def __init__(self, pipe):
				self._event = threading.Event()
				self._stopEvent = threading.Event()
				self._thread = threading.Thread(
					target=pipe._read_pipe_event,
					args=(self._event, self._stopEvent),
					daemon=True
				)
				self._thread.start()
				self._attached_watchdog_thread = None
			
			def stop(self):
				self._stopEvent.set()
			
			def isSet(self):
				return self._event.isSet()
			
			def clear(self):
				self._event.clear()
			
			def attach(self, function, args=()):
				#Run a function when Event is set. Automatically clears the event after function ran
				def _attached_watchdog(stopEvent, function, args):
					while not self._stopEvent.isSet():
						self._event.wait()
						function(*args)
						self._event.clear()
				
				self._attached_watchdog_thread = threading.Thread(
					target=_attached_watchdog,
					args=(self._stopEvent, function, args),
					daemon=True
				)
				self._attached_watchdog_thread.start()

			def detach(self):
				#a.k.a. stop this
				self._stopEvent.set()
			
			def is_attached(self):
				if self._attached_watchdog_thread is None:
					return False
				return self._attached_watchdog_thread.is_alive()
		
		return _PipeEvent(self)
