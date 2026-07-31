// Universal 20 mm payload grid, CERN-OHL-P-2.0
$fn=36; width=220; depth=180; thickness=5; grid=20; hole=4.4;
difference(){linear_extrude(thickness)offset(r=10)square([width-20,depth-20],center=true);for(x=[-80:grid:80])for(y=[-60:grid:60])translate([x,y,-1])cylinder(h=thickness+2,d=hole);}
