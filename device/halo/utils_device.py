def get_device_identifier():
  """
  Get a unique identifier for the device from CPU serial
  """
  cpuserial = "0000000000000000"
  try:
    f = open('/proc/cpuinfo','r')
    for line in f:
      if line[0:6]=='Serial':
        cpuserial = line[10:26]
    f.close()
  except:
    cpuserial = "ERROR000000000" 
  return cpuserial
  
