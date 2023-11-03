structure = [
	{
        "id" : "layer_count",
		"type" : "choices",
		"label" : "layer count",
		"choices" : ["1 layer", "2 layers", "4 layers"],
        "choices_data" : [1, 2, 4],
		"default" : 0,
        "datatype" : "int",
		"unit" : None
	},{
        "id" : "turns_count",
		"type" : "text",
		"label" : "turns per layer",
		"default" : 12,
        "datatype" : "int",
		"unit" : None
	},{
        "id" : "outer_diameter",
		"type" : "text",
		"label" : "outer diameter",
		"default" : 12.0,
        "datatype" : "float",
		"unit" : "mm"
	},{
        "id" : "turn_direction",
		"type" : "choices",
		"label" : "turn direction",
		"choices" : ["clockwise", "counter clockwise"],
        "choices_data" : [True, False],
		"default" : 0,
        "datatype" : "bool",
		"unit" : None
	},{
        "id" : "trace_width",
		"type" : "text",
		"label" : "trace width",
		"default" : 0.127,
        "datatype" : "float",
		"unit" : "mm"
	},{
        "id" : "trace_spacing",
		"type" : "text",
		"label" : "trace spacing",
		"default" : 0.127,
        "datatype" : "float",
		"unit" : "mm"
	},{
        "id" : "via_outer",
		"type" : "text",
		"label" : "via outer diameter",
		"default" : 0.6,
        "datatype" : "float",
		"unit" : "mm"
	},{
        "id" : "via_drill",
		"type" : "text",
		"label" : "via drill diameter",
		"default" : 0.3,
        "datatype" : "float",
		"unit" : "mm"
	}
]
