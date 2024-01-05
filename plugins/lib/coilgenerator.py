"""
This script is used to generate pcb coils
Copyright (C) 2022 Colton Baldridge
Copyright (C) 2023 Tim Goll

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import os
import math
from . import generator

TEMPLATE_FILE = "../dynamic/template.kicad_mod"
LAYER_TOP = "F.Cu"
LAYER_BOTTOM = "B.Cu"
LAYER_INNER = ["In1.Cu", "In2.Cu"]

BREAKOUT_LEN = 0.5  # (mm)

def generate(LAYER_COUNT, WRAP_CLOCKWISE, N_TURNS, TRACE_WIDTH, TRACE_SPACING, VIA_DIAMETER, VIA_DRILL, OUTER_DIAMETER, NAME, layer_names):
	class Connector:
		x: float
		y: float
		angle: float

		def __init__(self, x, y, angle):
			self.x = x
			self.y = y
			self.angle = angle
			self

	template_file = os.path.join(os.path.dirname(__file__), TEMPLATE_FILE)

	with open(template_file, "r") as file:
		template = file.read()

	arcs = []
	vias = []
	lines = []
	pads = []

	VIA_INSIDE_RADIUS = OUTER_DIAMETER / 2 - N_TURNS * TRACE_WIDTH - (N_TURNS - 1) * TRACE_SPACING - VIA_DIAMETER - TRACE_WIDTH / 2
	VIA_OUTSIDE_RADIUS = OUTER_DIAMETER / 2 + VIA_DIAMETER + TRACE_SPACING

	num_vias_inside = 0
	num_vias_outside = 0

	if LAYER_COUNT -1 > 0:
		num_vias_inside = (LAYER_COUNT -1) // 2
		num_vias_outside = num_vias_inside
		if (LAYER_COUNT -1) % 2 != 0:
			num_vias_inside += 1


		degree_steps_inside = 360 / (num_vias_inside)
		degree_steps_outside = 0
		if num_vias_outside != 0:
			degree_steps_outside = 360 / (num_vias_outside)

	arc_connectors = []

	# generating layer - 1 vias
	for v in range(0, LAYER_COUNT-1):

		# define if via is placed inside or outside of coil
		via_used_radius = VIA_INSIDE_RADIUS
		if v % 2 != 0:
			via_used_radius = VIA_OUTSIDE_RADIUS

		# set different step width for inside and outside loop
		degree_steps_used = degree_steps_inside
		if v % 2 != 0:
			degree_steps_used = degree_steps_outside

		rotation_degree = (v // 2) * degree_steps_used

		height = math.sin(math.radians(rotation_degree)) * via_used_radius
		width = math.sqrt(via_used_radius**2 - height**2)

		if rotation_degree > 90 and rotation_degree < 270:
			width *= -1

		arc_connectors.append(Connector(width, height, rotation_degree))

		vias.append(
			generator.via(
				generator.P2D(width, height),
				VIA_DIAMETER,
				VIA_DRILL
			)
		)

	# build out arcs to spec, until # turns is reached
	wrap_direction_multiplier = 1 if WRAP_CLOCKWISE else -1
	increment = TRACE_WIDTH + TRACE_SPACING

	start_radius = OUTER_DIAMETER / 2 - N_TURNS * TRACE_WIDTH - (N_TURNS - 1) * TRACE_SPACING
	for layer in range(LAYER_COUNT):
		current_radius = start_radius

		# for odd layers, the wrap direction needs to be flipped
		inverse_turn_mult = 1
		if layer % 2 != 0:
			inverse_turn_mult = -1

		#generate all full turns for one layer
		for _ in range(N_TURNS):
			arcs.extend(generator.loop(
					current_radius,
					increment,
					TRACE_WIDTH,
					layer_names[layer],
					wrap_direction_multiplier * inverse_turn_mult
				))
			current_radius += increment

	# draw breakout line(s)
	lines.append(
		generator.line(
			generator.P2D(current_radius, 0),
			generator.P2D(current_radius, BREAKOUT_LEN * -wrap_direction_multiplier),
			TRACE_WIDTH,
			LAYER_TOP
		)
	)
	lines.append(
		generator.line(
			generator.P2D(current_radius, BREAKOUT_LEN * -wrap_direction_multiplier),
			generator.P2D(current_radius + BREAKOUT_LEN, BREAKOUT_LEN * -wrap_direction_multiplier),
			TRACE_WIDTH,
			LAYER_TOP
		)
	)

	if LAYER_COUNT > 1:
		lines.append(
			generator.line(
				generator.P2D(current_radius, 0),
				generator.P2D(current_radius, BREAKOUT_LEN * wrap_direction_multiplier),
				TRACE_WIDTH,
				LAYER_BOTTOM
			)
		)
		lines.append(
			generator.line(
				generator.P2D(current_radius, BREAKOUT_LEN * wrap_direction_multiplier),
				generator.P2D(current_radius + BREAKOUT_LEN, BREAKOUT_LEN * wrap_direction_multiplier),
				TRACE_WIDTH,
				LAYER_BOTTOM
			)
		)

	# connect to pads

	# NOTE: there are some oddities in KiCAD here. The pad must be sufficiently far away from the last line such that
	# KiCAD does not display the "Cannot start routing from a graphic" error. It also must be far enough away that the
	# trace does not throw the "The routing start point violates DRC error". I have found that a 0.5mm gap works ok in
	# most scenarios, with a 1.2mm wide pad. Feel free to adjust to your needs, but you've been warned.
	pads.append(
		generator.pad(
			1,
			generator.P2D(current_radius + 1.7 * BREAKOUT_LEN, BREAKOUT_LEN * -wrap_direction_multiplier),
			8 * TRACE_WIDTH,
			TRACE_WIDTH,
			LAYER_TOP
		)
	)

	if LAYER_COUNT > 1:
		pads.append(
			generator.pad(
				2,
				generator.P2D(current_radius + 1.7 * BREAKOUT_LEN, BREAKOUT_LEN * wrap_direction_multiplier),
				8 * TRACE_WIDTH,
				TRACE_WIDTH,
				LAYER_BOTTOM
			)
		)

	substitution_dict = {
		"NAME": NAME,
		"LINES": ''.join(lines),
		"ARCS": ''.join(arcs),
		"VIAS": ''.join(vias),
		"PADS": ''.join(pads),
		"TIMESTAMP1": generator.tstamp(),
		"TIMESTAMP2": generator.tstamp(),
		"TIMESTAMP3": generator.tstamp(),
	}

	return template.format(**substitution_dict)
