{% load i18n %}

var origgetAvailableTableFilterst = getAvailableTableFilters;
getAvailableTableFilters = function(tableKey) {
     if(tableKey == 'stp_test'){
        return {
            testname: {
                title: '{% trans "Test Name" %}',
                description: '{% trans "Filter by test name" %}',
                options: testNameCodes,
            },
            teststatus: {
                title: '{% trans "Test Status" %}',
                options: [
                    {
                        key:'0',
                        value:'OK'
                    },
                    {
                        key:'1',
                        value:'KO'
                    }
                    ,
                    {
                        key:'2',
                        value:'Waiting'
                    }
                ]
            },
            lastdate:{
                title: '{% trans "Only Last Date" %}',
                type: 'bool'
            },
            date_greater:{
                title: '{% trans "Date Greater than" %}',
                type: 'date'
            },
            date_lesser:{
                title: '{% trans "Date Lesser than" %}',
                type: 'date'
            },

        };
     }
     
     return origgetAvailableTableFilterst(tableKey);
}


function STP_initPanel(){
    filterOption={
        download:true,
    }

    var filters = loadTableFilters('stp_test');
    var options={
        queryParams: filters,
        name:'stp_test',        
    }

    setupFilterList('stp_test', $('#STP_test_table'), '#filter-list-stp_test', filterOption);
    $('#STP_test_table').inventreeTable(options);
}

$(document).ready(function () {
    STP_initPanel();
})


