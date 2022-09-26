# Adding '3d sound' to Shadow Port
Hear loud sounds coming from different rooms in the same zone. Each zone will have it's own coordinates for each room.
When a loud sound is activated, all rooms in the zone are triggered to compare coords with the room that had the sound activated.
If the the adjacent rooms are close enough to hear the sound they send a message based on the sounds location like "From the NE you hear a loud bang!!"

Msg template: "<<far> Below/Above> you to the <distant> <s,n,se,sw,ne,nw> you hear <sound effect><! x power of sound><CAPITALIZE ENTIRE MESSAGE FOR VERY LOUD SOUNDS>""

Steps:
- Add zone tags to rooms.
- Add x,y and z coord attributes to rooms.
- Make a modified tunnel command that autofills coords.
- Make a new social commands file and add a yell command.

