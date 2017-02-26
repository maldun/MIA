==============================
MIA - MIA Is not an Assistant
==============================
    Copyright (C) 2017  Stefan Reiterer

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

Attempt to create my own virtual assistant

Programm Structure
==================

- Impressor: The Impressor handles the data input. It acts asan converter, which transmitts the necessary information to the processor in the form of events.

- Processor: The Processor is the part which converts the input events into output events. This is were the AI lives. The AI core is planned to be based on OpenAI

- Expressor: The Expressor takes the output event, and shows a reaction. They are either multimedia expressions, or working actions like sending an email
