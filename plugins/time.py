# 
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
# 
#        http://www.apache.org/licenses/LICENSE-2.0
# 
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import datetime
from api import command, message, plugin, database
from api.database.table import table, tableTypes
from api.database.entry import entry
from libs import displayname

def onInit(plugin_in):
    # Set Commands
    setoffset_command = command.command(plugin_in, 'setoffset', shortdesc='Set your UTC offset.')
    time_command = command.command(plugin_in, 'time', shortdesc='Get local time.')
    return plugin.plugin(plugin_in, 'time', [setoffset_command, time_command])

async def onCommand(message_in):
    database.init()
    OffsetTable = table('offsets', tableTypes.pGlobal)
    
    if message_in.command == 'setoffset':
        # Normalize offset
        offsetstr = message_in.body.strip()
        
        if offsetstr[0] == '+':
            prefix = '+'
        else:
            prefix = ''
        
        try:
            hours, minutes = map(int, offsetstr.split(':'))
        except Exception:
            try:
                hours = int(offsetstr)
                minutes = 0
            except Exception:
                return message.message('Incorrect Offset format. Has to be in +/-HH:MM!')
        normalizedoffset = '{}{}:{}'.format(prefix, hours, minutes)

        # Set Offset

        existingOffset = table.search(OffsetTable, 'id', '{}'.format(message_in.author.id))

        if existingOffset != None:
            existingOffset.edit(dict(id=message_in.author.id, offset=normalizedoffset))
        else:
            table.insert(OffsetTable, dict(id=message_in.author.id, offset=normalizedoffset))
        
        return message.message('Your UTC offset has been set to *{}!*'.format(normalizedoffset))

    
    if message_in.command == 'time':
        memberOrOffset = message_in.body.strip()
        print(memberOrOffset)
        # Check whose time we need (or if we got an offset)
        if not memberOrOffset:
            member = message_in.author
            print("Member set to message_in.author")
        else:
            # Try to get a user first
            member = displayname.memberForName(message_in.body.strip(), message_in.server)
            print("Finding Member...")
        
        if member:
            # We got one
            print("Member found!")
            existingOffset = table.search(OffsetTable, 'id', '{}'.format(message_in.author.id))
            offset = existingOffset.data.get[1]
        else:
            print("Member not found!")
            offset = memberOrOffset

        if offset == None:
            return message.message('Either the member didn\'t set an offset, or the offset provided was invalid')

        offset = offset.replace('+', '')

        # Split time string by : and get hour/minute values
        try:
            hours, minutes = map(int, offset.split(':'))
        except Exception:
            try:
                hours = int(offset)
                minutes = 0
            except Exception:
                return message.message('If a member was provided, then Database Corruption, else Invalid offset format.')

        msg = 'UTC'
        # Get the time
        t = datetime.datetime.utcnow()
        # Apply offset
        if hours > 0:
            # Apply positive offset
            msg += '+{}'.format(offset)
            td = datetime.timedelta(hours=hours, minutes=minutes)
            newTime = t + td
        elif hours < 0:
            # Apply negative offset
            msg += '{}'.format(offset)
            td = datetime.timedelta(hours=(-1*hours), minutes=(-1*minutes))
            newTime = t - td
        else:
            # No offset
            newTime = t

        if member:
            msg = '{}; where *{}* is, it\'s currently *{}*'.format(msg, displayname.name(member), newTime.strftime("%I:%M %p"))
        else:
            msg = '{} is currently *{}*'.format(msg, newTime.strftime("%I:%M %p"))
        # Say message
        return message.message(msg)