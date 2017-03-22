/*****************************************************************************
 *
 *    OpenERP, Open Source Management Solution
 *    Copyright (C) 2017 Solucións Aloxa S.L. <info@aloxa.eu>
 *    						Alexandre Díaz <alex@aloxa.eu>
 *
 *    This program is free software: you can redistribute it and/or modify
 *    it under the terms of the GNU Affero General Public License as
 *    published by the Free Software Foundation, either version 3 of the
 *    License, or (at your option) any later version.
 *
 *    This program is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *    GNU Affero General Public License for more details.
 *
 *    You should have received a copy of the GNU Affero General Public License
 *    along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 *****************************************************************************/
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
        
         console.log(this);
        
        this.ds_model = new data.DataSetSearch(this, this.view.model);
        this.model_product_prices_table = new Model("product.prices_table");
        this.model_view = new Model(this.view.model);
        
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
    	var self = this;
    	var values = [];
    	this.$el.find('.o_mdtable_item').each(function(){
    		var $this = $(this);
    		var _id = $this.data('id');
    		var _x = $this.data('x');
    		var _y = $this.data('y');
    		var _v = $this.find('input').val();
    		
    		if (self._get_item(_x, _y).value != _v) {
    			self.model_product_prices_table.call('write', [[_id], {'value': _v}]);
    			self._set_item(_x, _y, _v);
    		}
		});

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
    				var item = this._get_item(hx[x], hy[y]);
    				tbody_src += `<td class='o_mdtable_item' data-id='${item.id}' data-x='${item.pos_x}' data-y='${item.pos_y}'>${parseFloat(item.value).toFixed(2) || '0.00'}</td>`;
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
				var item = this._get_item(hx[x], false);
				tbody_src += `<td class='o_mdtable_item' data-id='${item.id}' data-x='${item.pos_x}' data-y='1'>${parseFloat(item.value).toFixed(2) || '0.00'}</td>`;
			}
		
	    	table.append(`<tbody><tr>${tbody_src}</tr></tbody>`);
    	}
    	table.appendTo(this.$el.empty());
    	this.bind_events();
    },
    
    bind_events: function () {
    	var self = this;
    	
    	$('.o_mdtable_item').on('click', function(ev){
    		var $this = $(this);
    		var inEditMode = self.view.get("actual_mode") === 'edit';
    		if (!inEditMode) {
    			var $button = $(document).find(".oe_form_button_edit");
                $button.openerpBounce();
                ev.stopPropagation();
                core.bus.trigger('click', ev);
    		}
    	});
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
    		if ((!item.pos_y && item.pos_x == x) || (item.pos_x == x && item.pos_y == y)) {
    			value = item;
    			return;
    		}
    	});
    	
    	return value;
    },
    
    _set_item(x, y, value) {
    	var self = this;
    	this.values.forEach(function(item, index) {
    		if ((!item.pos_y && item.pos_x == x) || (item.pos_x == x && item.pos_y == y)) {
    			item.value = value;
    			self.values[index] = item;
    			return;
    		}
    	});
    },
});

core.form_widget_registry.add('manzano_multi_dimension_table', MultiDimensionTable);

return MultiDimensionTable;
});