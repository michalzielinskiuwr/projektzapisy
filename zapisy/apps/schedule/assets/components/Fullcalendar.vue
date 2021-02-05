<template>
  <div>
    <Filters
        @refetchEvents="refetchEvents"
        ref="filtersComponent"/>
    <Reservation
        @refetchEvents="refetchEvents"
        @addEvent="addEvent"
        @unselect="unselect"
        @hideEventById="hideEventById"
        ref="reservationComponent"/>
    <FullCalendar :options="calendarOptions" ref="calendarComponent"/>
  </div>
</template>

<script>
import axios from "axios";
import FullCalendar from '@fullcalendar/vue'
import plLocale from "@fullcalendar/core/locales/pl";
import bootstrapPlugin from "@fullcalendar/bootstrap";
import interactionPlugin from "@fullcalendar/interaction";
import dayGridPlugin from "@fullcalendar/daygrid";
import timeGridPlugin from "@fullcalendar/timegrid";
import Reservation from "./Reservation.vue";
import Filters from "./Filters.vue";

// Sets header for all POST requests to enable CSRF protection.
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

const event_status = {
  "pending": "0",
  "accepted": "1",
  "rejected": "2"
};

const event_type = {
  "exam": "0",
  "test": "1",
  "event": "2",
  "class": "3",
  "other": "4",
  "special_reservation": "5"
};

const event_color = {
  "invisible": "#d3bb5a",
  "user_is_author": "#8ed35a",
  // Status colors are used in events' borders
  "pending": "#ff0",
  "accepted": "#0f0",
  "rejected": "#f00",
  // Type colors are used to mark events
  "type_test": "#539CDB",
  "type_exam": "#0588FA",
  "type_event": "#0423B0",
  "type_special_reservation": "#223487",
  "type_class": "#121F59"
};

export default {
  components: {
    FullCalendar, // make the <FullCalendar> tag available
    Reservation,
    Filters
  },
  data() {
    return {
      calendarOptions: {
        plugins: [interactionPlugin, timeGridPlugin, dayGridPlugin, bootstrapPlugin],

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
        events: this.fetchEvents,

        // Allow for selecting hours in the calendar to create events, print the block
        // showing that event. 'select' and 'eventClick' are references to Vue app
        // 'reservation' functions for creating and editing/viewing events.
        selectable: true,
        selectMirror: true,

        select: this.showCreateModal,
        eventClick: this.showEditViewModal
      }
    }
  },
  methods: {
    fetchEvents: async function (fetchInfo) {
      console.log("Is it in fullcalendar component?");
      let url = new URL("classrooms/terms/", window.location.origin);
      url.searchParams.set("start", fetchInfo.start.toISOString());
      url.searchParams.set("end", fetchInfo.end.toISOString());
      console.log("url: ", url);

      let usp = this.$refs.filtersComponent.create_searchparams();
      for (const [key, value] of usp)
        url.searchParams.set(key, value);

      console.log("url after: ", url);

      return $.getJSON(url, function (data) {
        for (let i = 0; i < data.length; i++) {
          // Set colors for fetched events
          switch (data[i]['type']) {
            case event_type.exam:
              data[i]['color'] = event_color.type_exam;
              break;
            case event_type.test:
              data[i]['color'] = event_color.type_test;
              break;
            case event_type.event:
              data[i]['color'] = event_color.type_event;
              break;
            case event_type.class:
              data[i]['color'] = event_color.type_class;
              break;
            case event_type.special_reservation:
              data[i]['color'] = event_color.type_special_reservation;
              break;
          }

          if (data[i]['visible'] == false)
            data[i]['color'] = event_color.invisible;

          switch (data[i]['status']) {
            case event_status.pending:
              data[i]['borderColor'] = event_color.pending;
              break;
            case event_status.accepted:
              data[i]['borderColor'] = event_color.accepted;
              break;
            case event_status.rejected:
              data[i]['borderColor'] = event_color.rejected;
              break;
          }
        }
      });
    },


    showCreateModal(timeRange) {
      console.log("show_modal_add called from Fullcalendar.vue");
      this.$refs.reservationComponent.show_modal_add(timeRange);
    },

    showEditViewModal(info) {
      console.log("show_modal_edit_or_view called from Fullcalendar.vue");
      this.$refs.reservationComponent.show_modal_edit_or_view(info);
    },

    test(arg) {
      console.log("test called, argument: ", arg);
      console.log(arg);
    },

    refetchEvents() {
      console.log("refetchEvents called in fullcalendar.vue");
      this.$refs.calendarComponent.getApi().refetchEvents();
    },

    addEvent(event) {
      console.log("addEvent called in fullcalendar.vue");
      console.log(event);
      this.$refs.calendarComponent.getApi().addEvent(event);
    },

    unselect() {
      this.$refs.calendarComponent.getApi().unselect();
    },

    hideEventById(event_id) {
      let event = this.$refs.calendarComponent.getApi().getEventById(event_id);
      if (event)
        event.remove();
    }
  },
}
</script>

<style scoped>
</style>