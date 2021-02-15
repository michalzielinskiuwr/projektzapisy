import axios from "axios";
import Vue from "vue/dist/vue.js";
import { Calendar } from "@fullcalendar/core";
import plLocale from "@fullcalendar/core/locales/pl";
import bootstrapPlugin from "@fullcalendar/bootstrap";
import interactionPlugin from "@fullcalendar/interaction";
import dayGridPlugin from "@fullcalendar/daygrid";
import timeGridPlugin from "@fullcalendar/timegrid";

// Sets header for all POST requests to enable CSRF protection.
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

const event_status = {
    "pending":  "0",
    "accepted": "1",
    "rejected": "2"
};

const event_type = {
    "exam":  "0",
    "test":  "1",
    "event": "2",
    "class": "3",
    "other": "4",
    "special_reservation": "5"
};

const event_color = {
    "new_event": "#ffc0cb",
    "invisible": "#d3bb5a",
    "user_is_author": "#8ed35a",
    "pending": "#ff0",
    "accepted": "#0f0",
    "rejected": "#f00",
    // Type colors are used to mark events
    "type_test":  "#539CDB",
    "type_exam":  "#0588FA",
    "type_event": "#0423B0",
    "type_special_reservation": "#223487",
    "type_class": "#121F59"
};

async function fetchEvents(fetchInfo) {
    let url = new URL("classrooms/terms/", window.location.origin);
    url.searchParams.set("start", fetchInfo.start.toISOString());
    url.searchParams.set("end", fetchInfo.end.toISOString());

    let room_id = $('#room_selector').val();
    if (room_id == "all")
        url.searchParams.delete('rooms');
    else
        url.searchParams.set("rooms", [room_id]);

    let title_author_input = $('#title_author_input').val();
    if (title_author_input)
        url.searchParams.set("title_author", title_author_input);

    var types = [];
    if ($('#exam_checkbox').is(':checked'))                 types.push(event_type.exam);
    if ($('#test_checkbox').is(':checked'))                 types.push(event_type.test);
    if ($('#event_checkbox').is(':checked'))                types.push(event_type.event);
    if ($('#classes_checkbox').is(':checked'))              types.push(event_type.class);
    if ($('#other_checkbox').is(':checked'))                types.push(event_type.other);
    if ($('#special_reservation_checkbox').is(':checked'))  types.push(event_type.special_reservation);

    if (types.length > 0)
        url.searchParams.set("types", types);
    else
        return [];

    var fetchedEvents = $.getJSON(url, function (data) {
        for (var i = 0; i < data.length; i++) {
            // Set colors for fetched events
            switch (data[i]['type']) {
                case event_type.exam:  data[i]['color'] = event_color.type_exam;  break;
                case event_type.test:  data[i]['color'] = event_color.type_test;  break;
                case event_type.event: data[i]['color'] = event_color.type_event; break;
                case event_type.class: data[i]['color'] = event_color.type_class; break;
                case event_type.other: data[i]['color'] = event_color.type_other; break;
                case event_type.special_reservation: data[i]['color'] = event_color.type_special_reservation; break;
            }

            if(data[i]['visible'] == false)
                data[i]['color'] = event_color.invisible;

            switch (data[i]['status']) {
                case event_status.pending: data[i]['borderColor'] = event_color.pending; break;
                case event_status.accepted: data[i]['borderColor'] = event_color.accepted; break;
                case event_status.rejected: data[i]['borderColor'] = event_color.rejected; break;
            }
        }
    });

    return fetchedEvents;
}

let calendarEl, calendar;

document.addEventListener("DOMContentLoaded", function() {
    calendarEl = document.getElementById("calendar");

    calendar = new Calendar(calendarEl, {
        plugins: [ interactionPlugin, timeGridPlugin, dayGridPlugin, bootstrapPlugin ],

        // Default settings for FullCalendar
        themeSystem: "bootstrap",
        eventDisplay: 'block',
        initialView: "timeGridWeek",
        locale: plLocale,
        timeZone: "UTC",
        height: "auto",

        // Allow clicking in day and week names, determine time range displayed
        navLinks: true,
        allDaySlot: false,
        slotMinTime: "08:00:00",
        slotMaxTime: "22:00:00",

        // Define which buttons should be displayed for navigation and calendar display types
        headerToolbar: {
            start: "prev,next today",
            center: "title",
            end: "timeGridDay,timeGridWeek,dayGridMonth",
        },

        // buttonText is a text displayed in "prev" and "next" keys, these are arrows empty inside
        buttonText: {
            prev: "\u25C1",
            next: "\u25B7",
        },

        // Display date in format day - full month name - year
        titleFormat: {
            day: "numeric",
            month: "long",
            year: "numeric"
        },

        // events are fetched from database using function fetchEvents (defined above)
        events: fetchEvents,

        // Allow for selecting hours in the calendar to create events, print the block
        // showing that event. 'select' and 'eventClick' are references to Vue app
        // 'reservation' functions for creating and editing/viewing events.
        selectable: true,
        selectMirror: true,
        select: reservation.show_modal_add,
        eventClick: reservation.show_modal_edit_or_view
    });

    calendar.render();

    $('#filters').find('input, select').on('change, input', function () {
        calendar.refetchEvents();
    })

    // After closing reservation modal, clear all modal's fields and remove temporary event
    // from FullCalendar (always with id "temp").
    $('#reservation').on('hidden.bs.modal', function () {
        reservation.clear_and_hide_modal();
        if (calendar.getEventById("temp"))
            calendar.getEventById("temp").remove();
    });
});

const reservation = new Vue({
    delimiters: ['[[', ']]'], // otherwise there are template conflicts with Django
    el: '#reservation',
    data: {
        author: "",
        name: "",
        description: "",
        visible: true,
        type: "2",
        status: "0",
        terms: [],

        options: {
            visible: [
                { value: true,  text: 'Tak'},
                { value: false, text: 'Nie'},
            ],
            type: [
                { value: "0", text: "Egzamin" },
                { value: "1", text: "Kolokwium" },
                { value: "2", text: "Wydarzenie" },
                { value: "5", text: "Rezerwacja cykliczna" }
            ],
            status: [
                { value: "0", text: "Oczekujące" },
                { value: "1", text: "Zaakceptowane" },
                { value: "2", text: "Odrzucone" },
            ]
        },

        edit_or_view: false,
        url: ""
    },
    methods: {
        // This modal is displayed only when adding event, it supports either adding events
        // by clicking the "Create event" button and selecting hours in FullCalendar
        show_modal_add: function (timeRange) {
            this.edit_or_view = false; // do not print extra fields (available in edit/view modes only)
            $('#reservation').modal('show');

            if (timeRange != null) {
                // timeRange is argument received from FullCalendar by selecting event's hours
                var start = new Date(timeRange.startStr).toISOString();
                var end   = new Date(timeRange.endStr).toISOString();

                this.add_term();
                // Get the day in YYYY-MM-DD format and start and end in HH-MM format
                this.terms[0].day = start.slice(0, 10);
                this.terms[0].start = start.slice(11, 16);
                this.terms[0].end = end.slice(11, 16);

                // If user wants to make a reservation in "Month" view, startStr and endStr
                // are equal to 00:00, so make the term to be since 8 AM to 10 PM.
                if (this.terms[0].start == "00:00") this.terms[0].start = "08:00";
                if (this.terms[0].end   == "00:00") this.terms[0].end   = "22:00";

                // Display temporary event in the calendar which corresponds to selected hours
                calendar.addEvent({
                    id: "temp",
                    title: "Nowe wydarzenie (wstępny termin)",
                    start: start,
                    end: end,
                    color: event_color.new_event
                });
                calendar.unselect();
            }
        },

        // This modal is used both in editing an event and displaying its properties
        // (for people without permissions), it is opened by clicking an event in calendar.
        show_modal_edit_or_view: function (info) {
            // When user wants to see properties of classes, return from the function
            // and user will be redirected to the group's list.
            if (info.event.url.includes("course"))
                return;

            this.edit_or_view = true;
            info.jsEvent.preventDefault();

            // Get data from given URL and save it in fields of reservation app.
            $.getJSON(info.event.url, function (event) {
                reservation.author = event.author;
                reservation.name = event.title;
                reservation.description = event.description;
                reservation.type = event.type;
                reservation.status = event.status;
                reservation.visible = event.visible;
                reservation.url = event.url;

                for (let term of event.terms) {
                    // Make sure that if the place of an event is not any of the classrooms
                    // in the institute, it selects right option in <select> (as the input
                    // for the place is displayed when only 'room_none' is active.
                    if (term.rooms == null)
                        term.rooms = ['room_none'];

                    // We need to get rid of seconds to send data properly (expected format
                    // is HH:MM, but fetched data is in format HH:MM:SS).
                    term.start = term.start.length == 5 ? term.start : term.start.slice(0, 5);
                    term.end =   term.end.length == 5 ? term.end : term.end.slice(0, 5);
                }

                reservation.terms = event.terms;
            });

            $('#reservation').modal('show');
        },

        // Empty all data fields used in the form and close the modal, used basically
        // to prepare the modal for next uses.
        clear_and_hide_modal: function () {
            this.author = "",
            this.name = "";
            this.description = "";
            this.type = "2";
            this.status = "0";
            this.visible = true;
            this.terms = [];
            this.url = "";

            $('#reservation').modal('hide');
        },

        // Add a term row in the add/edit event modal
        add_term: function () {
            var elem = document.createElement('tr');
            this.terms.push({
                day: "",
                start: "",
                end: "",
                place: "",
                rooms: [],
                ignore_conflicts_rooms: []
            });
        },

        // Remove a term row from in the add/edit event modal
        remove_term: function (index) {
            this.terms.splice(index, 1);
        },

        // Send reservation's data in POST request, so it gets saved in database.
        add_to_db: function () {
            for (let term of this.terms)
                if (term.place != "")
                    delete term.rooms;

            axios.post("events/", {
                "title": this.name,
                "description": this.description,
                "visible": this.visible,
                "type": this.type,
                "terms": this.terms
            })
            .then(function (response) { console.log(response); calendar.refetchEvents(); })
            .catch(function (error) { console.log("Creating event failed"); });

            this.clear_and_hide_modal();
            calendar.refetchEvents();
        },

        // Send edited reservation's data in POST
        edit_in_db: function () {
            for (let term of this.terms)
                if (term.rooms.includes('room_none'))
                    term.rooms = [];

            axios.post(this.url, {
                "title": this.name,
                "description": this.description,
                "visible": this.visible,
                "status": this.status,
                "type": this.type,
                "terms": this.terms
            })
                .then(function () { calendar.refetchEvents(); })
                .catch(function (error) { console.log("Creating event failed"); });

            this.clear_and_hide_modal();
        },

        // Remove event with given URL from database
        remove_from_db: function (url) {
            if (!url)
                return;

            axios.post('delete-event/' + parseInt(url.match(/\d+/)) + '/')
                .then(function () { calendar.refetchEvents(); })
                .catch(function (error) { console.log("Deleting event failed"); });

            this.clear_and_hide_modal();
        }
    },
});

// A lot has to be done here, there is nothing implemented yet (only template in html)
const filters = new Vue({
    delimiters: ['[[', ']]'],
    el: '#filter',
    data: {
        collapsed: false,
        title_or_author: "",
        rooms: [ "all" ],
        place: "",
        types: [ "0", "1", "2", "5" ],
        statuses: [ "0", "1", "2" ],
        visible: [],

        options: {
            visible: [
                { value: true,  text: 'Tak'},
                { value: false, text: 'Nie'},
            ],
            type: [
                { value: "0", text: "Egzamin" },
                { value: "1", text: "Kolokwium" },
                { value: "2", text: "Wydarzenie" },
                { value: "3", text: "Zajęcia" },
                // value "4" is for deprecated type OTHER, but there are no events with this type
                { value: "5", text: "Rezerwacja cykliczna" }
            ],
            status: [
                { value: "0", text: "Oczekujące" },
                { value: "1", text: "Zaakceptowane" },
                { value: "2", text: "Odrzucone" },
            ]
        },
    },

    methods: {

    },

    watch: {

    }
});