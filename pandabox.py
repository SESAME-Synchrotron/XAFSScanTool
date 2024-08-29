from pandablocks.commands import Put, Arm, Disarm
from pandablocks.blocking import BlockingClient
# from pandablocks.asyncio import AsyncioClient
# from pandablocks.hdf import write_hdf_files

class PandA:
	def __init__(self, host) -> None:
		self.pandaboxHost = host

	def _send(self, command):
		try:
			with BlockingClient(self.pandaboxHost) as cli:
				cli.send(command)
		except Exception as e:
			print(f'An error occurred: {e}')
			raise AttributeError

	def arm(self):
		self._send(Arm())

	def disarm(self):
		self._send(Disarm())

	def disableBit(self, bit):
		self._send(Put(f"BITS1.{bit.upper()}", 0))

	def enableBit(self, bit):
		self._send(Put(f"BITS1.{bit.upper()}", 1))
	
	def encoderSetp(self, val):
		self._send(Put(f"INENC1.SETP", val))

	def pulse(self, blockID, width, pulses):
		self._send(Put(f"PULSE{blockID}.WIDTH", width))
		self._send(Put(f"PULSE{blockID}.PULSES", pulses))

	# async def PCAP(self, fileName):
	# 	async with AsyncioClient(self.pandaboxHost) as cli:
	# 		await write_hdf_files(cli, file_names=iter([str(fileName)]))

	def sendTable(self, blockID, repeats, trigger,
					positions, time1, phase1, time2, phase2):
		"""
			sendTable: send an array of positions to the sequencer (SEQ) table.
				- blockID: SEQ block number (1, 2).
				- repeats: Row repeats.
				- trigger: {0: 'Immediate',
							 1: 'bita=0',
							 2: 'bita=1',
							 3: 'bitb=0',
							 4: 'bitb=1',
							 5: 'bitc=0',
							 6: 'bitc=1',
							 7: 'posa>=position',
							 8: 'posa<=position',
							 9: 'posb>=position',
							 10: 'posb<=position',
							 11: 'posc>=position',
							 12: 'posc<=position'}
				- positions: List of positions.
				- time1: phase1 duration.
				- phase1: ['OUTF1', 'OUTE1', 'OUTD1', 'OUTC1', 'OUTB1', 'OUTA1'] ==> [0, 1, 1, 0, 1, 1]
				- time2: phase2 duration.
				- phase2: ['OUTF2', 'OUTE2', 'OUTD2', 'OUTC2', 'OUTB2', 'OUTA2'] ==> [0, 1, 1, 0, 1, 1]
		"""

		# binary representation
		repeatsB = f'{repeats:016b}'    # 16 bits (0:15)
		triggerB = f'{trigger:04b}'     # 4 bits (16:19)
		phase1B = ''                    # 6 bits (20:25)
		phase1.reverse()
		phase1B = ''.join('1' if value else '0' for value in phase1)
		phase2.reverse()
		phase2B = ''                    # 6 bits (26:31)
		phase2B = ''.join('1' if value else '0' for value in phase2)

		codeB = phase2B + phase1B + triggerB + repeatsB  # 32 bits code
		code = int(codeB, 2)
		positions = positions if isinstance(positions, list) else [positions]
		tableContent = []
		for pos in positions:
			tableContent.extend([f'{code}', f'{pos}', f'{time1}', f'{time2}'])

		self._send(Put(f'SEQ{blockID}.PRESCALE', 0))
		self._send(Put(f'SEQ{blockID}.REPEATS', 1))
		self._send(Put(f'SEQ{blockID}.TABLE', tableContent))
