#!/usr/bin/lua
-- Read-only UCI configuration; the slider only overrides the white LED at runtime.
local nixio = require('nixio')
local led = '/sys/class/leds/white:status/'
local function read(path)
 local f = io.open(path, 'r')
 if not f then return '' end
 local value = f:read('*a'); f:close(); return value or ''
end
local function write(path, value)
 local f = io.open(path, 'w')
 if f then f:write(value); f:close() end
end
local function off()
 if not read(led..'trigger'):find('%[none%]') then write(led..'trigger', 'none') end
 if read(led..'brightness'):match('%d+') ~= '0' then write(led..'brightness', '0') end
end
local previous, config = nil, nil
while true do
 local state = nil
 for line in read('/sys/kernel/debug/gpio'):gmatch('[^\n]+') do
  if line:match('|mode%s*%)') then state = line:match('%s(lo)%s') or line:match('%s(hi)%s'); break end
 end
 local current = read('/etc/config/system')
 if state == 'hi' then
  if state ~= previous or current ~= config then
   os.execute('/etc/init.d/led start white:status >/dev/null 2>&1')
  end
 else
  off()
 end
 previous, config = state, current
 write('/tmp/kwrt-led-slider-state', state == 'hi' and 'on\n' or state == 'lo' and 'off\n' or 'unavailable-off\n')
 nixio.nanosleep(1, 0)
end
