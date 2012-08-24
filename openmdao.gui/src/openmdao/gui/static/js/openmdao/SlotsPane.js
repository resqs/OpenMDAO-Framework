
var openmdao = (typeof openmdao === "undefined" || !openmdao ) ? {} : openmdao ;

openmdao.SlotsPane = function(elm,model,pathname,name,editable) {

    /***********************************************************************
     *  private
     ***********************************************************************/

    // initialize private variables
    var self = this,
        figures = {},
        slotsID = pathname.replace(/\./g,'-')+"-slots",
        slotsDiv = jQuery('<div style="position:relative; background-color:black;">')
            .appendTo(elm);

    self.pathname = pathname;

    elm.css({'overflow':'auto'});

    /** update slots by recreating figures from JSON slots data
     *  TODO: prob just want to iterate through & update existing figures
     */
    function updateFigures(json) {
        jQuery.each(json, function(idx,slot) {
            debug.info('SlotsPane.updateFigures() slot',idx,slot);
            if (figures[slot.name]) {
                figures[slot.name].setState(slot.klass, slot.filled);
            }
            else {
                var fig = openmdao.SlotFigure(model, pathname+'.'+slot.name,
                                              slot.containertype, slot.klass,
                                              slot.desc, slot.filled);
                figures[name] = fig;
                slotsDiv.append(fig);
            }
        });
    }

    // all this is just to prevent drops from falling thru to underlying panes
    var true_dropdiv = slotsDiv.parent();
    true_dropdiv.data('corresponding_openmdao_object',this);
    openmdao.drag_and_drop_manager.addDroppable(true_dropdiv);

    true_dropdiv.droppable ({
        accept: '.objtype',
        out: function(ev,ui) {
            var o = true_dropdiv.data('corresponding_openmdao_object');
            openmdao.drag_and_drop_manager.draggableOut(true_dropdiv);
        },
        over: function(ev,ui) {
            openmdao.drag_and_drop_manager.draggableOver(true_dropdiv);
        },
        drop: function(ev,ui) {
            /* divs could be in front of divs and the div that gets the drop
               event might not be the one that is in front visibly and therefore
               is not the div the user wants the drop to occur on */
            var o = elm.data('corresponding_openmdao_object');
            top_div = openmdao.drag_and_drop_manager.getTopDroppableForDropEvent(ev,ui);
            /* call the method on the correct div to handle the drop */
            if (top_div) {
                var drop_function = top_div.droppable('option','actualDropHandler');
                drop_function(ev,ui);
            }
        }
    });

    // TODO: Do I really need these ?
    this.highlightAsDropTarget=function() {
        debug.info ("highlight slotspane", slotsDiv[0].id ) ;
    };

    this.unhighlightAsDropTarget=function() {
        debug.info ("unhighlight slotspane", slotsDiv[0].id ) ;
    };

    /***********************************************************************
     *  protected
     ***********************************************************************/

    /** update slots diagram */
    this.loadData = function(json) {
        slotsDiv.html('');
        figures = {};
        if (Object.keys(json).length > 0) {
            updateFigures(json);
        }
    };
};
