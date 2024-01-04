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

def generate(LAYER_COUNT, WRAP_CLOCKWISE, N_TURNS, TRACE_WIDTH, TRACE_SPACING, VIA_DIAMETER, VIA_DRILL, OUTER_DIAMETER, NAME):
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

		vias.append(
			generator.via(
				generator.P2D(width, height),
				VIA_DIAMETER,
				VIA_DRILL
			)
		)

	current_radius = OUTER_DIAMETER / 2 - N_TURNS * TRACE_WIDTH - (N_TURNS - 1) * TRACE_SPACING


	# build out arcs to spec, until # turns is reached
	wrap_multiplier = 1 if WRAP_CLOCKWISE else -1
	increment = TRACE_WIDTH + TRACE_SPACING

	for arc in range(N_TURNS):
		if arc == 0:
			# Front Layer
			arcs.extend(generator.arc(
				generator.P2D(current_radius - VIA_DIAMETER, 0),
				generator.P2D(-VIA_DIAMETER, -wrap_multiplier * (current_radius - VIA_DIAMETER / 2)),
				generator.P2D(-current_radius, 0),
				TRACE_WIDTH,
				LAYER_TOP,
				bool(wrap_multiplier + 1)
			))
			arcs.extend(generator.arc(
				generator.P2D(-current_radius, 0),
				generator.P2D(-increment / 2, wrap_multiplier * (current_radius + increment / 2)),
				generator.P2D(current_radius + increment, 0),
				TRACE_WIDTH,
				LAYER_TOP,
				bool(wrap_multiplier + 1)
			))

			if LAYER_COUNT > 1:
				layer = LAYER_BOTTOM # top to bottom if 2 layers

				if LAYER_COUNT > 2:
					layer = LAYER_INNER[0] # top to inner1 if more than two layers

				arcs.extend(generator.arc(
					generator.P2D(current_radius - VIA_DIAMETER, 0),
					generator.P2D(-VIA_DIAMETER, wrap_multiplier * (current_radius - VIA_DIAMETER / 2)),
					generator.P2D(-current_radius, 0),
					TRACE_WIDTH,
					layer,
					not bool(wrap_multiplier + 1)
				))
				arcs.extend(generator.arc(
					generator.P2D(-current_radius, 0),
					generator.P2D(-increment / 2, -wrap_multiplier * (current_radius + increment / 2)),
					generator.P2D(current_radius + increment, 0),
					TRACE_WIDTH,
					layer,
					not bool(wrap_multiplier + 1)
				))

			if LAYER_COUNT > 2:
				arcs.extend(generator.loop(
					current_radius,
					increment,
					TRACE_WIDTH,
					LAYER_INNER[1],
					wrap_multiplier
				))
				arcs.extend(generator.arc(
					generator.P2D(current_radius, 0),
					generator.P2D(VIA_DIAMETER, wrap_multiplier * (current_radius - VIA_DIAMETER / 2)),
					generator.P2D(-current_radius + VIA_DIAMETER, 0),
					TRACE_WIDTH,
					LAYER_INNER[1],
					not bool(wrap_multiplier + 1)
				))

				arcs.extend(generator.loop(
					current_radius,
					increment,
					TRACE_WIDTH,
					LAYER_BOTTOM,
					-wrap_multiplier
				))
				arcs.extend(generator.arc(
					generator.P2D(current_radius, 0),
					generator.P2D(VIA_DIAMETER, -wrap_multiplier * (current_radius - VIA_DIAMETER / 2)),
					generator.P2D(-current_radius + VIA_DIAMETER, 0),
					TRACE_WIDTH,
					LAYER_BOTTOM,
					bool(wrap_multiplier + 1)
				))

		elif arc == N_TURNS - 1 and LAYER_COUNT > 2:
			# inner layer 0 extended lines
			arcs.extend(generator.arc(
				generator.P2D(OUTER_DIAMETER / 2 + VIA_DIAMETER + TRACE_SPACING, 0),
				generator.P2D(VIA_DIAMETER + TRACE_SPACING, -wrap_multiplier * (OUTER_DIAMETER / 2 + (VIA_DIAMETER + TRACE_SPACING) / 2 - TRACE_WIDTH)),
				generator.P2D(-(OUTER_DIAMETER - TRACE_WIDTH - TRACE_SPACING) / 2, 0),
				TRACE_WIDTH,
				LAYER_INNER[0],
				bool(wrap_multiplier + 1)
			))
			arcs.extend(generator.arc(
				generator.P2D(-(OUTER_DIAMETER - TRACE_WIDTH - TRACE_SPACING) / 2, 0),
				generator.P2D(VIA_DIAMETER + TRACE_SPACING, wrap_multiplier * (OUTER_DIAMETER / 2 - (TRACE_WIDTH + TRACE_SPACING) / 2)),
				generator.P2D((OUTER_DIAMETER - TRACE_WIDTH - TRACE_SPACING) / 2, 0),
				TRACE_WIDTH,
				LAYER_INNER[0],
				bool(wrap_multiplier + 1)
			))

			# inner layer 1 extended lines
			arcs.extend(generator.arc(
				generator.P2D(OUTER_DIAMETER / 2 + VIA_DIAMETER + TRACE_SPACING, 0),
				generator.P2D(VIA_DIAMETER + TRACE_SPACING, wrap_multiplier * (OUTER_DIAMETER / 2 + (VIA_DIAMETER + TRACE_SPACING) / 2)),
				generator.P2D(-(OUTER_DIAMETER - TRACE_WIDTH - TRACE_SPACING) / 2, 0),
				TRACE_WIDTH,
				LAYER_INNER[1],
				not bool(wrap_multiplier + 1)
			))
			arcs.extend(generator.arc(
				generator.P2D(-(OUTER_DIAMETER - TRACE_WIDTH - TRACE_SPACING) / 2, 0),
				generator.P2D(VIA_DIAMETER + TRACE_SPACING, -wrap_multiplier * (OUTER_DIAMETER / 2 - (TRACE_WIDTH + TRACE_SPACING) / 2)),
				generator.P2D((OUTER_DIAMETER - TRACE_WIDTH - TRACE_SPACING) / 2, 0),
				TRACE_WIDTH,
				LAYER_INNER[1],
				not bool(wrap_multiplier + 1)
			))

			# add back top/bottom layers
			arcs.extend(generator.loop(
				current_radius,
				increment,
				TRACE_WIDTH,
				LAYER_TOP,
				wrap_multiplier
			))

			arcs.extend(generator.loop(
				current_radius,
				increment,
				TRACE_WIDTH,
				LAYER_BOTTOM,
				-wrap_multiplier
			))
		else:
			arcs.extend(generator.loop(
				current_radius,
				increment,
				TRACE_WIDTH,
				LAYER_TOP,
				wrap_multiplier
			))

			if LAYER_COUNT > 1:
				arcs.extend(generator.loop(
					current_radius,
					increment,
					TRACE_WIDTH,
					LAYER_BOTTOM,
					-wrap_multiplier
				))

			if LAYER_COUNT > 2:
				arcs.extend(generator.loop(
					current_radius,
					increment,
					TRACE_WIDTH,
					LAYER_INNER[0],
					-wrap_multiplier
				))

				arcs.extend(generator.loop(
					current_radius,
					increment,
					TRACE_WIDTH,
					LAYER_INNER[1],
					wrap_multiplier
				))

		current_radius += increment

	# draw breakout line(s)
	lines.append(
		generator.line(
			generator.P2D(current_radius, 0),
			generator.P2D(current_radius, BREAKOUT_LEN * -wrap_multiplier),
			TRACE_WIDTH,
			LAYER_TOP
		)
	)
	lines.append(
		generator.line(
			generator.P2D(current_radius, BREAKOUT_LEN * -wrap_multiplier),
			generator.P2D(current_radius + BREAKOUT_LEN, BREAKOUT_LEN * -wrap_multiplier),
			TRACE_WIDTH,
			LAYER_TOP
		)
	)

	if LAYER_COUNT > 1:
		lines.append(
			generator.line(
				generator.P2D(current_radius, 0),
				generator.P2D(current_radius, BREAKOUT_LEN * wrap_multiplier),
				TRACE_WIDTH,
				LAYER_BOTTOM
			)
		)
		lines.append(
			generator.line(
				generator.P2D(current_radius, BREAKOUT_LEN * wrap_multiplier),
				generator.P2D(current_radius + BREAKOUT_LEN, BREAKOUT_LEN * wrap_multiplier),
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
			generator.P2D(current_radius + 1.7 * BREAKOUT_LEN, BREAKOUT_LEN * -wrap_multiplier),
			8 * TRACE_WIDTH,
			TRACE_WIDTH,
			LAYER_TOP
		)
	)

	if LAYER_COUNT > 1:
		pads.append(
			generator.pad(
				2,
				generator.P2D(current_radius + 1.7 * BREAKOUT_LEN, BREAKOUT_LEN * wrap_multiplier),
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
