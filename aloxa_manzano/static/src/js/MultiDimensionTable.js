odoo.define('aloxa_manzano.MultiDimensionTableField', function (require) {
"use strict";

var ajax = require('web.ajax');
var config = require('web.config');
var core = require('web.core');
var data = require('web.data');
var Dialog = require('web.Dialog');
var Model = require('web.Model');
var form_common = require('web.form_common');
var framework = require('web.framework');
var session = require('web.session');

var _t = core._t;
var qweb = core.qweb;

var MultiDimensionTable = form_common.AbstractField.extend({
	_MODE : { TABLE_1D:'table_1d', TABLE_2D:'table_2d' },

	
    template: 'aloxa_manzano.MultiDimensionTableView',

    init: function () {
        this._super.apply(this, arguments);

        this.tableType_field = this.node.attrs.mode || false;
        
        this.ds_model = new data.DataSetSearch(this, this.view.model);
        this.model_product_prices_table = new Model("product.prices_table");
        
        this.isInvisible = true;
        this.values = [];
    },

    start: function () {
        // use actual_mode property on view to know if the view is in create mode anymore
        this.view.on("change:actual_mode", this, this.on_check_visibility_mode);
        this.view.on('view_content_has_changed', this, this.on_view_changed);
        this.on_check_visibility_mode();
        return this._super();
    },
    
    commit_value: function (value_) {
    	this.$el.find('.o_mdtable_item').each(function(){
			console.log(value_);
		});
    	
    	//this.model_product_prices_table.call('write', []
        console.log("INTERNAL SET value");
        return this._super();
    },
    
    read_value: function () {
        var self = this;
        
        this.model_product_prices_table.call('search_read', [[['id', 'in', this.get_value()]]])
        	.then(function(results){
        		self.values = results;
        		self.render_value();
        	});
    },
    
    set_value: function(value_) {
    	var _super = this._super(value_);
    	this.read_value();
    	return _super;
    },
    
    render_value: function () {
    	if (!this.isInvisible) {
	    	var self = this;
	    	
	    	this.ds_model.read_ids([this.view.datarecord.id], [this.tableType_field])
	        .then(function (results) {
	            self.tableType = results[0][self.tableType_field];
	            self.render_widget();
	        });
    	}
    },
    
    render_widget: function () {    	
    	if (typeof this.values === 'undefined')
    		return;
    	
    	var table = $('<table>');
    	table.addClass('col-md-12');
    	
    	// Get Headers
		var hx = [],
			hy = [];
		this.values.forEach(function(item, index) {
			hx.push(item.pos_x);
			hy.push(item.pos_y);
		});
		hx = [...new Set(hx)];
		hy = [...new Set(hy)];
		///
		
		// Table HTML
    	if (this.tableType == this._MODE.TABLE_2D) {
    		var thead_src = '<th>&nbsp;</th>';
    		for (var i in hx) { thead_src += `<th>${hx[i]}</th>`; }
    		table.append(`<thead><tr>${thead_src}</tr></thead>`);
    		
    		var tbody_src = '';
    		for (var y in hy) {
    			tbody_src += `<tr><th class='col-md-1'>${hy[y]}</th>`;
    			for (var x in hx) {
    				tbody_src += `<td class='o_mdtable_item' data-x='${hx[x]}' data-y='${hy[y]}'>${this._get_item(hx[x], hy[y]).value || '0.0'}</td>`;
    			}
    			tbody_src += '</tr>';
    		}
	    	table.append(`<tbody>${tbody_src}</tbody>`);
    	} else {
    		var thead_src = '';
    		for (var i in hx) { thead_src += `<th>${hx[i]}</th>`; }
    		table.append(`<thead><tr>${thead_src}</tr></thead>`);
    		
			var tbody_src = '';
			for (var x in hx) {
				tbody_src += `<td>${this._get_item(hx[x], hy[0]).value || '0.0'}</td>`;
			}
		
	    	table.append(`<tbody><tr>${tbody_src}</tr></tbody>`);
    	}
    	table.appendTo(this.$el.empty());
    	this.bind_events();
    },
    
    bind_events: function () {
    	var self = this;
    	
    	/*$('.o_mdtable_item').on('click', function(ev){
    		console.log(this.dataset);
    		var $this = $(this);
    		var inEditMode = self.view.get("actual_mode") === 'edit';
    		if (inEditMode && !$this.find('input')[0]) {
    			$this.html(`<input type='text' value='${$this.text()}' />`);
    		}
    	});*/
    },
    
    on_view_changed: function () {
    	var self = this;
    	
    	/*this.ds_model.read_ids([this.view.datarecord.id], [this.tableType_field])
        .then(function (results) {
            if (self.tableType !== results[0][self.tableType_field]) {
            	self.render_widget();
            }
        });*/
    },
    
    on_check_visibility_mode: function () {
    	this.isInvisible = this.view.get("actual_mode") === 'create';
    	
    	var inEditMode = this.view.get("actual_mode") === 'edit';
		this.$el.find('.o_mdtable_item').each(function(){
			var $this = $(this);
			if (inEditMode) {
				$this.html(`<input type='text' value='${$this.text()}' />`);
			} else {
				$this.text($this.find('input').val());
			}
		});
    },
    
    
    _get_item(x, y) {
    	var value = false;
    	this.values.forEach(function(item, index) {
    		if (item.pos_x == x && item.pos_y == y) {
    			value = item;
    			return;
    		}
    	});
    	
    	return value;
    },
});

core.form_widget_registry.add('manzano_multi_dimension_table', MultiDimensionTable);

return MultiDimensionTable;
});