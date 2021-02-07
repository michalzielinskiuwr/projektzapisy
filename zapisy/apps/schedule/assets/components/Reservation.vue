<template>
  <div>
    <div class="modal fade" tabindex="-1" role="dialog" id="reservation_modal" ref="modal_ref">
      <div class="modal-dialog modal-lg modal-dialog-centered" role="document">
        <div v-if="!user_info.is_admin && !(user_info.full_name == author) && edit_or_view" class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Informacje o wydarzeniu</h5>
            <button type="button" class="close" data-dismiss="modal">
              <span>&times;</span>
            </button>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <label>Autor wydarzenia</label>
              <input type="text" class="form-control" v-model="author" disabled>
            </div>

            <div class="form-group">
              <label>Nazwa wydarzenia</label>
              <input class="form-control" v-model="name" disabled>
            </div>

            <div class="form-group">
              <label>Opis wydarzenia</label>
              <textarea class="form-control" v-model="description" disabled></textarea>
            </div>

            <div class="form-group">
              <label>Typ wydarzenia</label>
              <select v-model="type" class="form-control" disabled>
                <option v-for="option in options.type" v-bind:value="option.value">
                  {{ option.text }}
                </option>
              </select>
            </div>

            <table class="table table-sm table-striped">
              <thead>
              <tr>
                <td><strong>Dzień</strong></td>
                <td><strong>Początek</strong></td>
                <td><strong>Koniec</strong></td>
                <td><strong>Miejsce</strong></td>
              </tr>
              </thead>
              <tbody>
              <tr v-for="(term, index) in terms">
                <td><p>{{ term.day }}</p></td>
                <td><p>{{ term.start }}</p></td>
                <td><p>{{ term.end }}</p></td>
                <td v-if="term.place == '' || term.place == null">
                  Sale: <p v-for="room in term.rooms" style="display: inline;">{{ room }} </p>
                </td>
                <td v-else>
                  {{ term.place }}
                </td>
              </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div v-else class="modal-content">
          <div class="modal-header">
            <h5 v-if="!edit_or_view" class="modal-title">Utwórz wydarzenie</h5>
            <h5 v-else-if="edit_or_view && user_info.is_admin || user_info.full_name == author">
              Edytuj wydarzenie
            </h5>
            <button type="button" class="close" data-dismiss="modal">
              <span>&times;</span>
            </button>
          </div>
          <div class="modal-body">
            <div class="form-group" v-if="edit_or_view">
              <label>Autor wydarzenia</label>
              <input type="text" class="form-control" v-model="author" disabled>
            </div>

            <div class="form-group">
              <label>Nazwa wydarzenia</label>
              <input class="form-control" placeholder="Seminarium ANL" v-model="name">
              <b v-if="!name">Wprowadź nazwę wydarzenia!</b>
            </div>

            <div class="form-group">
              <label>Opis wydarzenia</label>
              <textarea class="form-control" placeholder="Co będzie się działo?" v-model="description"></textarea>
              <b v-if="!description">Wprowadź opis wydarzenia!</b>
            </div>

            <div class="form-group">
              <label>Wydarzenie widoczne dla wszystkich użytkowników</label>
              <select v-model="visible" class="form-control">
                <option v-for="option in options.visible" v-bind:value="option.value">
                  {{ option.text }}
                </option>
              </select>
            </div>

            <div class="form-group" v-if="user_info.is_admin || user_info.is_employee">
              <label>Typ wydarzenia</label>
              <select v-model="type" class="form-control">
                <option v-for="option in options.type" v-bind:value="option.value">
                  {{ option.text }}
                </option>
              </select>
            </div>

            <div class="form-group">
              <label>Status wydarzenia</label>
              <select v-model="status" class="form-control" v-if="user_info.is_admin">
                <option v-for="option in options.status" v-bind:value="option.value">
                  {{ option.text }}
                </option>
              </select>
              <select v-model="status" class="form-control" disabled v-else>
                <option v-for="option in options.status" v-bind:value="option.value">
                  {{ option.text }}
                </option>
              </select>
            </div>

            <table class="table">
              <thead>
              <tr>
                <td class="align-middle"><strong>Dzień</strong></td>
                <td class="align-middle"><strong>Godziny</strong></td>
                <td class="align-middle" style="width: 50%"><strong>Miejsce</strong></td>
                <td class="align-middle"><strong>Interakcja</strong></td>
              </tr>
              </thead>
              <tbody>
              <tr v-for="(term, index) in terms" v-bind:key="term.id">
                <td><input class="form-control" type="date" v-model="term.day"> </td>
                <td>
                    <input class="form-control" type="time" step="60" v-model="term.start">
                    <input class="form-control" type="time" step="60" v-model="term.end">
                </td>
                <td>
                  <div class="dropdown dropup">
                    <button class="btn btn-secondary dropdown-toggle" type="button" id="dropdownMenuButton" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                      Wybierz miejsce
                    </button>
                      
                    <div class="dropdown-menu scrollable-menu" aria-labelledby="dropdownMenuButton" v-model="term.rooms">

                    <!--<div class="progress bg-light" style="height: 35px;">
                      <div role="progressbar" class="progress-bar bg-primary" style="width: 0%;">  
                      </div>
                      <div role="progressbar" class="progress-bar bg-secondary progress-bar-striped" style="width: 85.7143%;">
                        Zajęte
                      </div>
                      <div role="progressbar" class="progress-bar bg-transparent" style="width: 14.2857%;">
                      </div>
                    </div>-->
                      
                           <!--v-for="progressbar_info in progressbars_info[term][room.number]" v-bind:key="progressbar_info.id"-->


                      <div class="dropdown-item" v-bind:class="{ active: term.place }">Miejsce poza instytutem</div>
                      <input type="text" class="form-control" v-model="term.place" placeholder="Sala HS w Instytucie Matematyki">

                      <button class="dropdown-item" style="outline: none" v-for="room in options.rooms" v-bind:key="room.number"
                          v-bind:class="{ active: term.rooms && term.rooms.includes(room.number) }" 
                          v-on:click="add_or_remove_room_from_term(term, room)">
                        <div class="progress bg-light" style="height: 14px;">
                          <div role="progressbar" class="progress-bar"
                           v-for="progressbar_info in progressbars_info[room.number]" v-bind:key="progressbar_info.id"
                           v-bind:class="progressbar_info.class" v-bind:style="{ width: progressbar_info.width }">
                           </div>
                        </div>
                        <div >
                          {{ room.number }} ({{ room.capacity }} miejsc, {{ room.type }})
                        </div>
                      </button>
                    </div>
                  </div>
                  <!--<div v-if="term.rooms.length === 1 && term.rooms.includes('room_none')">
                    <br>
                    <input type="text" class="form-control" v-model="term.place"
                           placeholder="Sala HS w Instytucie Matematyki">
                  </div>
                  <select class="custom-select" v-model="term.rooms" title="Wybierz sale" multiple>
                    <option value="room_none">Miejsce poza II</option>
                    <option v-for="room in options.rooms" :value="room.number">
                      {{ room.number }} ({{ room.capacity }} miejsc, {{ room.type }})
                    </option>
                  </select>
                  <div v-if="term.rooms.length === 1 && term.rooms.includes('room_none')">
                    <br>
                    <input type="text" class="form-control" v-model="term.place"
                           placeholder="Sala HS w Instytucie Matematyki">
                  </div> -->
                </td>
                <td>
                  <button class="btn btn-info" data-toggle="collapse" style="margin-bottom: 5px;"
                          :data-target="'#conflicts' + index">
                    Konflikty
                  </button>

                  <div :id="'conflicts' + index" class="collapse">
                    <div v-for="room in term.rooms">
                      <input type="checkbox" :value="room" v-model="term.ignore_conflicts_rooms">
                      <label>{{ room }}</label>
                    </div>
                  </div>
                  <button v-on:click="remove_term(index);" class="btn btn-danger">Usuń</button>
                </td>
              </tr>
              </tbody>
            </table>
            <div>
              <button class="btn btn-primary" @click="add_term">Dodaj termin</button>
            </div>
          </div>
          <div class="modal-footer" v-if="edit_or_view">
            <button type="button" class="btn btn-secondary" data-dismiss="modal">Anuluj</button>
            <button type="button" class="btn btn-danger" @click="remove_from_db(url)">Usuń wydarzenie</button>
            <button type="button" class="btn btn-success" @click="edit_in_db">Edytuj wydarzenie</button>
          </div>
          <div class="modal-footer" v-else>
            <button type="button" class="btn btn-secondary" data-dismiss="modal">Anuluj</button>
            <button type="button" class="btn btn-success" @click="add_to_db">Utwórz wydarzenie</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";

axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

export default {
  name: "Reservation",
  data() {
    return {
      toogleme: false,
      author: "",
      name: "",
      description: "",
      visible: true,
      type: "2",
      status: "0",
      terms: [],

      options: {
        visible: [
          {value: true, text: 'Tak'},
          {value: false, text: 'Nie'},
        ],
        type: [
          {value: "0", text: "Egzamin"},
          {value: "1", text: "Kolokwium"},
          {value: "2", text: "Wydarzenie"},
          {value: "5", text: "Rezerwacja cykliczna"}
        ],
        status: [
          {value: "0", text: "Oczekujące"},
          {value: "1", text: "Zaakceptowane"},
          {value: "2", text: "Odrzucone"},
        ],
        rooms: []
      },

      edit_or_view: false,
      url: "",
      user_info: {
        full_name: "",
        is_student: false,
        is_employee: false,
        is_admin: false
      },
      progressbar_color_classes: {empty:"bg-light", occupied:"bg-secondary", reserve:"bg-success", conflict:"bg-danger"},
      progressbars_info: {}
    }
  },
  mounted() {
    // If reservation modal closes by any way, reload all modal's data and remove
    // temporary event in calendar (used on creating events)
    $(this.$refs.modal_ref).on("hidden.bs.modal", this.clear_and_hide_modal);
  },
  created: function () {
    this.fetch_data_from_html();
  },
  methods: {
    fetch_data_from_html: function () {
      // Data for classrooms and user is sent by Django templates, thus we need
      // to retrieve it and save it, so we can use it everywhere in this component.
      this.options.rooms = JSON.parse(document.getElementById("classrooms").innerHTML);
      for (let room of this.options.rooms){
        room.active = false;
      }
      this.user_info = JSON.parse(document.getElementById("user_info").innerHTML);
    },

    fill_progressbars_info: function(terms){
      //console.log(this.options.rooms);
      for (let room of this.options.rooms){
        this.$set(this.progressbars_info, room.number, [{width:"30%", class:"bg-light"}, {width:"70%", class:"bg-success"}]);
      }
      //console.log(this.progressbars_info);
    },

    add_or_remove_room_from_term: function(term, room){
      if (!term.rooms){
        term.rooms = [room.number];
        return;
      }
      const index = term.rooms.indexOf(room.number);
      if (index > -1) 
        term.rooms.splice(index, 1);
      else
        term.rooms.push(room.number);
    },

    // Functions with fc_ prefix are shorthands for emitting methods in the
    // Fullcalendar component, as it is the only possibility to call them.
    fc_add_event: function (event_obj) {
      this.$emit('addEvent', event_obj);
    },

    fc_unselect: function () {
      this.$emit('unselect');
    },

    fc_hide_event_by_id: function (event_id) {
      this.$emit('hideEventById', event_id);
    },

    fc_refetch_events: function () {
      this.$emit('refetchEvents');
    },

    // This modal is displayed only when adding event, it supports either adding events
    // by clicking the "Create event" button and selecting hours in FullCalendar
    show_modal_add: function (timeRange) {
      // this.clear_and_hide_modal();
      console.log("show_modal_add called from Reservation.vue");
      this.edit_or_view = false; // do not print extra fields (available in edit/view modes only)
      $('#reservation_modal').modal('show');

      if (timeRange != null) {
        // timeRange is argument received from FullCalendar by selecting event's hours
        let start = new Date(timeRange.startStr).toISOString();
        let end = new Date(timeRange.endStr).toISOString();

        this.add_term();
        // Get the day in YYYY-MM-DD format and start and end in HH-MM format
        this.terms[0].day = start.slice(0, 10);
        this.terms[0].start = start.slice(11, 16);
        this.terms[0].end = end.slice(11, 16);

        // If user wants to make a reservation in "Month" view, startStr and endStr
        // are equal to 00:00, so make the term to be since 8 AM to 10 PM.
        if (this.terms[0].start == "00:00") this.terms[0].start = "08:00";
        if (this.terms[0].end == "00:00") this.terms[0].end = "22:00";

        // Display temporary event in the calendar which corresponds to selected hours
        this.fc_add_event({
          id: "temp",
          title: "Nowe wydarzenie (wstępny termin)",
          start: start,
          end: end,
          color: "pink"
        });

        this.fc_unselect();
      }
    },

    // This modal is used both in editing an event and displaying its properties
    // (for people without permissions), it is opened by clicking an event in calendar.
    show_modal_edit_or_view: async function (info) {
      console.log("show_modal_edit_or_view called from Reservation.vue");
      // When user wants to see properties of classes, return from the function
      // and user will be redirected to the group's list.
      if (info.event.url.includes("course"))
        return;

      this.edit_or_view = true;
      info.jsEvent.preventDefault();

      // Get data from given URL and save it in fields of reservation app. We
      // need to save the reference to 'this', otherwise in the body of getJSON
      // we would not be able to set values of Reservation's fields.
      let reservation = this;
      await $.getJSON(info.event.url, function (event) {
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
          //if (term.rooms == null || !term.rooms)
          //  term.rooms = ['room_none'];

          // We need to get rid of seconds to send data properly (expected format
          // is HH:MM, but fetched data is in format HH:MM:SS).
          term.start = term.start.length == 5 ? term.start : term.start.slice(0, 5);
          term.end = term.end.length == 5 ? term.end : term.end.slice(0, 5);

          term.ignore_conflicts = !(term.ignore_conflicts_rooms == null || !term.ignore_conflicts_rooms);
        }
        reservation.terms = event.terms;
      });
      this.fill_progressbars_info(this.terms);
      $('#reservation_modal').modal('show');
    },

    // Empty all data fields used in the form and close the modal, used basically
    // to prepare the modal for next uses.
    clear_and_hide_modal: async function () {
      this.fc_hide_event_by_id('temp');
      await this.fc_refetch_events();

      this.author = "";
      this.name = "";
      this.description = "";
      this.type = "2";
      this.status = "0";
      this.visible = true;
      this.terms = [];
      this.url = "";

      $('#reservation_modal').modal('hide');
    },

    // Add a term row in the add/edit event modal
    add_term: function () {
      let elem = document.createElement('tr');
      this.terms.push({
        day: "",
        start: "",
        end: "",
        place: "",
        rooms: [],
        ignore_conflicts: false,
        ignore_conflicts_rooms: [],
      });
    },

    // Remove a term row from in the add/edit event modal
    remove_term: function (index) {
      this.terms.splice(index, 1);
    },

    // Send reservation's data in POST request, so it gets saved in database.
    add_to_db: async function () {
      //for (let term of this.terms)
       // if (term.place != "")
        //  delete term.rooms;

      await axios.post("events/", {
        "title": this.name,
        "description": this.description,
        "visible": this.visible,
        "type": this.type,
        "terms": this.terms
      })
          .then(function (response) {
            console.log(response);
            alert("Wydarzenie utworzono pomyślnie");
          })
          .catch(function (error) {
            console.log("Creating event failed", error);
            alert("Nie udało się utworzyć wydarzenia");
          });

      this.clear_and_hide_modal();
    },

    // Send edited reservation's data in POST
    edit_in_db: async function () {
     // for (let term of this.terms)
     //   if (term.rooms.includes('room_none'))
     //     term.rooms = [];

      // If user who is not an admin tries to edit an event, its status has to be
      // changed to "pending" - otherwise unprivileged users would not be able to
      // edit events created by them.
      await axios.post(this.url, {
        "title": this.name,
        "description": this.description,
        "visible": this.visible,
        "status": this.user_info.is_admin ? this.status : "0",
        "type": this.type,
        "terms": this.terms
      })
          .then(function (response) {
            console.log(response);
            alert("Edycja wydarzenia wykonana");
          })
          .catch(function (error) {
            console.log("Creating event failed", error);
            alert("Edycja wydarzenia zakończona niepowodzeniem");
          });

      this.clear_and_hide_modal();
    },

    // Remove event with given URL from database
    remove_from_db: async function (url) {
      if (!url)
        return;

      await axios.post('delete-event/' + parseInt(url.match(/\d+/)) + '/')
          .then(function (response) {
            console.log(response);
            alert("Wydarzenie usunięto pomyślnie");
          })
          .catch(function (error) {
            console.log("Deleting event failed", error);
            alert("Nie udało się usunąć wydarzenia");
          });

      this.clear_and_hide_modal();
    },
  }
}
</script>

<style scoped>

.scrollable-menu {
    height: auto;
    max-height: 400px;
    overflow-x: hidden;
}

.dropdown:hover .dropdown-menu {
    white-space: nowrap;
    display: block;
    margin-bottom: 0; /* remove the gap so it doesn't close */
 }

select[multiple] {
  height: 35px !important;
  transition: height 0.5s;
}

select[multiple]:focus {
  height: 120px !important;
}
</style>