<template>
  <div>
    <div class="modal fade" tabindex="-1" role="dialog" id="reservation_modal" ref="modal_ref">
      <div class="modal-dialog modal-lg modal-dialog-centered" role="document">

        <div class="modal-content">
          <div class="modal-header">
            <h5 v-if="!edit_or_view" class="modal-title">
              Utwórz wydarzenie
            </h5>
            <h5 v-else-if="edit_or_view && user_has_permissions()" class="modal-title">
              Edytuj wydarzenie
            </h5>
            <h5 v-else class="modal-title">
              Informacje o wydarzeniu
            </h5>
            <button type="button" class="close" data-dismiss="modal">
              <span>&times;</span>
            </button>
          </div>
          <div class="modal-body">
            <div class="alert alert-danger alert-message" role="alert" v-if="show_alert">{{ error_message }}</div>
            <fieldset :disabled="edit_or_view && !user_has_permissions()">
            <div class="form-group" v-if="edit_or_view">
              <label for="author">Autor wydarzenia</label>
              <input type="text" class="form-control" id="author" v-model="author" disabled>
            </div>

            <div class="form-group">
              <label for="name">Nazwa wydarzenia</label>
              <input class="form-control" placeholder="Seminarium ANL" id="name" v-model="name">
            </div>

            <div class="form-group">
              <label for="description">Opis wydarzenia</label>
              <textarea class="form-control" placeholder="Co będzie się działo?" id="description" v-model="description"></textarea>
            </div>

            <div class="form-group" v-if="field_is_editable()">
              <label for="visibility">Wydarzenie widoczne dla wszystkich użytkowników</label>
              <select v-model="visible" class="form-control" id="visibility">
                <option v-for="option in options.visible" v-bind:value="option.value">
                  {{ option.text }}
                </option>
              </select>
            </div>

            <div class="form-group" v-if="edit_or_view || user_info.is_admin || user_info.is_employee">
              <label for="type">Typ wydarzenia</label>
              <select id="type" v-model="type" class="form-control" :disabled="!(user_info.is_admin || user_info.is_employee)">
                <option v-for="option in options.type" v-bind:value="option.value" :disabled="option.value === '5'">
                  {{ option.text }}
                </option>
              </select>
            </div>

            <div class="form-group" v-if="edit_or_view && user_has_permissions()">
              <label for="status">Status wydarzenia</label>
              <select id="status" v-model="status" class="form-control" :disabled="!user_info.is_admin">
                <option v-for="option in options.status" v-bind:value="option.value">
                  {{ option.text }}
                </option>
              </select>
            </div>

            <table class="table">
              <thead>
              <tr>
                <td class="align-middle"><strong>Dzień</strong></td>
                <td class="align-middle"><strong>Początek</strong></td>
                <td class="align-middle"><strong>Koniec</strong></td>
                <td class="align-middle"><strong>Miejsce</strong></td>
                <td class="align-middle" v-if="field_is_editable()"></td>
                <td v-if="field_is_editable()"></td>
              </tr>
              </thead>
              <tbody>
              <tr v-for="(term, index) in terms" v-bind:key="term.id">
                <td><input class="form-control" type="date" v-model="term.day"> </td>
                <td>
                    <input class="form-control" type="time" step="60" v-model="term.start">
                </td>
                <td>
                    <input class="form-control" type="time" step="60" v-model="term.end">
                </td>
                <td>
                  <div class="dropdown dropup" v-if="field_is_editable()">
                    <button class="btn btn-secondary dropdown-toggle" type="button" id="dropdownMenuButton" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                      Wybierz
                    </button>

                    <div class="dropdown-menu scrollable-menu" aria-labelledby="dropdownMenuButton" v-model="term.rooms">
                      <div class="dropdown-item" v-bind:class="{ active: term.place }">Miejsce poza instytutem</div>
                      <input type="text" class="form-control" v-model="term.place" placeholder="Sala HS w Instytucie Matematyki">

                      <button class="dropdown-item term" style="outline: none; border: 1px solid black; max-height: 60px !important;" v-for="room in options.rooms" v-bind:key="room.number"
                          v-bind:class="{ active: term.rooms && term.rooms.includes(room.number) }"
                          v-on:click="add_or_remove_room_from_term(term, room)">
                        <div class="progress bg-light term-bar" style="height: 14px;" v-if="!isFetching_progressbars_terms">
                          <div role="progressbar" class="progress-bar"
                           v-for="progressbar_info in progressbars_info[index][room.number][0]" v-bind:key="progressbar_info.id"
                           v-bind:class="progressbar_info.class" v-bind:style="{ width: progressbar_info.width }">
                          </div>
                        </div>
                        <div class="progress bg-light term-free" style="height: 14px;" v-if="!isFetching_progressbars_terms">
                          <div role="progressbar" class="progress-bar" style="visibility: visible"
                           v-for="progressbar_info in progressbars_info[index][room.number][1]" v-bind:key="progressbar_info.id"
                           v-bind:class="progressbar_info.class" v-bind:style="{ width: progressbar_info.width }">
                          </div>
                        </div>
                        <div class="progress bg-light term-occupied" style="height: 14px;" v-if="!isFetching_progressbars_terms">
                          <div role="progressbar" class="progress-bar" style="visibility: visible"
                           v-for="progressbar_info in progressbars_info[index][room.number][2]" v-bind:key="progressbar_info.id"
                           v-bind:class="progressbar_info.class" v-bind:style="{ width: progressbar_info.width }">
                          </div>
                        </div>
                        <div class="row" style="font-family: monospace;">
                          <div class="d-flex flex-row justify-content-between" style="width: 100%;">
                            <div>08:00</div>
                            <div>10:00</div>
                            <div>12:00</div>
                            <div>14:00</div>
                            <div>16:00</div>
                            <div>18:00</div>
                            <div>20:00</div>
                            <div>22:00</div>
                          </div>
                        </div>
                        <div>
                          {{ room.number }} ({{ room.capacity }} miejsc, {{ room.type }})
                        </div>
                      </button>
                    </div>
                  </div>
                  <div v-if="term.rooms.length > 0">
                    Sale:
                    <p v-for="(room, index) in term.rooms" :key="index" style="display:inline">
                      {{ room }}
                    </p>
                  </div>
                  <div v-if="term.place">
                    Miejsce poza II:
                    {{ term.place }}
                  </div>
                </td>
                <td v-if="field_is_editable()">
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
                </td>
                <td v-if="field_is_editable()">
                  <button v-on:click="remove_term(index);" class="btn btn-danger">-</button>
                </td>
              </tr>
              </tbody>
            </table>
            <div v-if="field_is_editable()">
              <button class="btn btn-primary" @click="add_term">Dodaj termin</button>
            </div>
            </fieldset>
          </div>
          <div class="modal-footer" v-if="!edit_or_view">
            <button type="button" class="btn btn-secondary" data-dismiss="modal">Anuluj</button>
            <button type="button" class="btn btn-success" @click="check_inputs_and_add_to_db">Utwórz wydarzenie</button>
          </div>
          <div class="modal-footer" v-else-if="edit_or_view && user_has_permissions()">
            <button type="button" class="btn btn-secondary" data-dismiss="modal">Anuluj</button>
            <button type="button" class="btn btn-danger" @click="remove_from_db(url)">Usuń wydarzenie</button>
            <button type="button" class="btn btn-success" @click="check_inputs_and_edit_in_db">Edytuj wydarzenie</button>
          </div>
          <div class="modal-footer" v-else>
            <button type="button" class="btn btn-secondary" data-dismiss="modal">Anuluj</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import dayjs from "dayjs";
const utc = require('dayjs/plugin/utc')
const isSameOrAfter = require('dayjs/plugin/isSameOrAfter');
const customParseFormat = require('dayjs/plugin/customParseFormat');
dayjs.extend(utc);
dayjs.extend(isSameOrAfter);
dayjs.extend(customParseFormat);

axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";
axios.defaults.xsrfCookieName = "csrftoken";

export default {
  name: "Reservation",
  data() {
    return {
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
      show_alert: false,
      error_message: "",

      url: "",
      user_info: {
        full_name: "",
        is_student: false,
        is_employee: false,
        is_admin: false
      },
      progressbar_color_classes: {
        empty:"bg-transparent",
        occupied:"bg-secondary",
        reserve:"bg-success",
        collision:"bg-danger"
      },
      progressbars_info: [],
      progressbars_terms: {},
      isFetching_progressbars_terms: false,
      // do not change when user change terms, needed for progressbars (for unclicked reserved term)
      original_terms: []
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
  watch: {
    terms: {
      handler: function(){
        if (this.terms.length){
          let dates_changed = false;
          for (let term of this.terms){
            if (term.day && !(term.day in this.progressbars_terms)){
              dates_changed = true;
              this.isFetching_progressbars_terms = true;
              this.fill_progressbars_terms().then( _ => {
                this.fill_progressbars_info();
                this.isFetching_progressbars_terms = false;
              });
              break;
            }
          }
          if (!dates_changed)
            this.fill_progressbars_info();
        }
      },
      deep: true
    }
  },
  methods: {
    fetch_data_from_html: function () {
      // Data for classrooms and user is sent by Django templates, thus we need
      // to retrieve it and save it, so we can use it everywhere in this component.
      this.options.rooms = JSON.parse(document.getElementById("classrooms").innerHTML);
      for (let room of this.options.rooms)
        room.active = false;

      this.user_info = JSON.parse(document.getElementById("user_info").innerHTML);
    },

    // Get from API all terms that occur in same days as event days.
    fill_progressbars_terms: async function(){
      let url = new URL("classrooms/chosen-days-terms/", window.location.origin);
      let days = "";
      for (let term of this.terms){
        days += term.day + ",";
      }
      url.searchParams.set("days", days);

      await axios.get(url).then((r) => {
        this.progressbars_terms = r.data;
      });
    },

    // Calculate progress bars width and class (color) for every term and room.
    fill_progressbars_info: function(){
      this.progressbars_info = [];
      // for every term
      for (let [index, term] of this.terms.entries()){
        this.progressbars_info.push({});
        // for every room in term
        for (let room of this.options.rooms){
          // Make progressbar layers (other terms, chosen term, conflicts).
          // Each layer will hold list of objects with progressbar width and class (define color)
          this.progressbars_info[index][room.number] = [[], [], []];
        }
      }
      // we will calculate only hours and minutes, but need full date object
      let now = dayjs().format('YYYY-MM-DD');
      for (let [index, term] of this.terms.entries()){
        // Add first progressbar layer - occupied hours from other terms
        for (let room in this.progressbars_terms[term.day]){
          // if terms with same hours duplicate, omit only one
          let self_term_hours_omitted = false;
          let room_progressbar_info = [{start: dayjs(now + "08:00"), end: dayjs(now + "22:00"), color: "empty"}];
          for (let term_hours of this.progressbars_terms[term.day][room]){
            // do not make collision with self
            if (this.original_terms[index] !== undefined &&
                this.original_terms[index].rooms.includes(room) &&
                term_hours[0].slice(0, 5) == this.original_terms[index].start &&
                term_hours[1].slice(0, 5) == this.original_terms[index].end &&
                !self_term_hours_omitted){
              self_term_hours_omitted = true;
              continue;
            }
            // If term hours collide, remove empty progressbar after colliding hours and merge colliding term hours
            if (room_progressbar_info.length > 1 &&
                room_progressbar_info[room_progressbar_info.length - 1].start.isSameOrAfter(dayjs(now + term_hours[0]))){
              room_progressbar_info.pop();
              let collision = room_progressbar_info[room_progressbar_info.length - 1];
              collision.start = collision.start.isBefore(dayjs(now + term_hours[0])) ? collision.start : dayjs(now + term_hours[0]);
              collision.end = collision.end.isAfter(dayjs(now + term_hours[1])) ? collision.end : dayjs(now + term_hours[1]);
            }else{
              room_progressbar_info[room_progressbar_info.length - 1].end = dayjs(now + term_hours[0]);
              room_progressbar_info.push({start: dayjs(now + term_hours[0]),  end: dayjs(now + term_hours[1]), color: "occupied"});
              room_progressbar_info.push({start: dayjs(now + term_hours[1]),  end: dayjs(now + "22:00"), color: "empty"});
            }
          }
          this.progressbars_info[index][room][0] = room_progressbar_info;
        }
        // Add second progressbar layer - reserved hours from chosen start and end
        for (let room of term.rooms){
          this.progressbars_info[index][room][1] = [
            {start: dayjs(now + "08:00"), end: dayjs(now + term.start), color: "empty"},
            {start: dayjs(now + term.start), end: dayjs(now + term.end), color: "reserve"},
            {start: dayjs(now + term.end), end: dayjs(now + "22:00"), color: "empty"}
          ];
        }
        // Add third progressbar layer - collisions
        for (let room of term.rooms){
          let room_progressbar_collisions = [{start: dayjs(now + "08:00"), end: dayjs(now + "22:00"), color: "empty"}]
          let curr_term_start = dayjs(now + term.start);
          let curr_term_end = dayjs(now + term.end);

          for (let first_layer_term_info of this.progressbars_info[index][room][0]){
            if (first_layer_term_info.color == "occupied" &&
                first_layer_term_info.start.isBefore(curr_term_end) &&
                first_layer_term_info.end.isAfter(curr_term_start)){
                  let collision = {color: "collision"};
                  if (first_layer_term_info.start.isBefore(curr_term_start))
                    collision.start = curr_term_start;
                  else
                    collision.start = first_layer_term_info.start;
                  if (first_layer_term_info.end.isAfter(curr_term_end))
                    collision.end = curr_term_end;
                  else
                    collision.end = first_layer_term_info.end;
                  room_progressbar_collisions[room_progressbar_collisions.length - 1].end = collision.start;
                  room_progressbar_collisions.push(collision);
                  room_progressbar_collisions.push({
                    start: collision.end,
                    end: dayjs(now + "22:00"),
                    color: "empty"});
                }
          }
          this.progressbars_info[index][room][2] = room_progressbar_collisions;
        }
      }
      // Change progressbar terms hours to width parameter and color string to proper progressbar class
      for (let progressbar_info of this.progressbars_info){
        for (let room in progressbar_info){
          for (let layer of progressbar_info[room]){
            for (let term_info of layer){
              // between 8:00 - 22:00 is 14 hours * 60 minutes
              term_info.width = (term_info.end.diff(
                  term_info.start, "minutes", true) /
                  (14 * 60) * 100).toFixed(2) + "%";
              term_info.class = this.progressbar_color_classes[term_info.color];
            }
          }
        }
      }
    },

    add_or_remove_room_from_term: function(term, room){
      if (!term.rooms){
        term.rooms = [room.number];
        return;
      }
      let index = term.rooms.indexOf(room.number);
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

    user_has_permissions: function () {
      return this.user_info.is_admin || this.user_info.full_name == this.author;
    },

    field_is_editable: function() {
      // Editable fields are visible only when user wants to create event or
      // when user has permissions to edit it (is admin or event author).
      return !this.edit_or_view || this.user_has_permissions();
    },

    // This modal is displayed only when adding event, it supports either adding events
    // by clicking the "Create event" button and selecting hours in FullCalendar
    show_modal_add: function (timeRange) {
      this.clear_modal();
      this.edit_or_view = false; // do not print extra fields (available in edit/view modes only)
      $('#reservation_modal').modal('show');

      if (timeRange != null) {
        // timeRange is argument received from FullCalendar by selecting event's hours
        let start = new Date(timeRange.startStr).toISOString();
        let end = new Date(timeRange.endStr).toISOString();

        this.add_term();
        // Get the day in YYYY-MM-DD format and start and end in HH-MM format
        this.terms[0].day = dayjs(start).format("YYYY-MM-DD");
        this.terms[0].start = dayjs(start).utc().format("HH:mm");
        this.terms[0].end = dayjs(end).utc().format("HH:mm");

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
      // When user wants to see properties of classes, return from the function
      // and user will be redirected to the group's list.
      if (info.event.url.includes("course"))
        return;

      this.clear_modal();
      this.edit_or_view = true;
      info.jsEvent.preventDefault();

      // Get data from given URL and save it in fields of reservation app.
      await axios.get(info.event.url).then((event) => {
        this.author = event.data.author;
        this.name = event.data.title;
        this.description = event.data.description;
        this.type = event.data.type;
        this.status = event.data.status;
        this.visible = event.data.visible;
        this.url = event.data.url;

        for (let term of event.data.terms) {
          // We need to get rid of seconds to send data properly (expected format
          // is HH:MM, but fetched data is in format HH:MM:SS).
          term.start = dayjs(term.start, "HH:mm").format("HH:mm")
          term.end = dayjs(term.end, "HH:mm").format("HH:mm")

          term.ignore_conflicts = !(term.ignore_conflicts_rooms == null || !term.ignore_conflicts_rooms);
        }
        this.terms = event.data.terms;
        // deep copy of terms, needed for progress bars
        this.original_terms = JSON.parse(JSON.stringify(event.data.terms));
      });

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
      this.progressbars_info = [],
      this.progressbars_terms = {},
      this.isFetching_progressbars_terms = false,
      this.original_terms = []

      $('#reservation_modal').modal('hide');
    },

    clear_modal: function () {
      this.author = "";
      this.name = "";
      this.description = "";
      this.type = "2";
      this.status = "0";
      this.visible = true;
      this.terms = [];
      this.error_message = "";
      this.show_alert = false;
      this.url = "";
      this.progressbars_info = [];
      this.progressbars_terms = {};
      this.isFetching_progressbars_terms = false;
      this.original_terms = [];
    },

    hide_modal: function () {
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
      this.original_terms.splice(index, 1);
    },

    check_inputs: function () {
      if (this.name && this.description)
        return true;

      let errors = "";
      if (!this.name)
        errors += "Nie wprowadzono nazwy wydarzenia.\n";

      if (!this.description)
        errors += "Nie wprowadzono opisu wydarzenia.\n";

      this.error_message = errors;
      this.show_alert = true;
      return false;
    },

    // Send reservation's data in POST request, so it gets saved in database.
    add_to_db: async function () {
      let that = this; // without it, closing modal without errors is impossible
      await axios.post("events/", {
        "title": this.name,
        "description": this.description,
        "visible": this.visible,
        "type": this.type,
        "terms": this.terms
      })
          .then(function (response) {
            that.hide_modal();
          })
          .catch(function (error) {
            that.show_alert = true;
            if (error.response.status == 400) {
              if (Array.isArray(error.response.data) && error.response.data.length) {
                // returned JSON with conflicts
                let conflicts = "";
                for (const conflict of error.response.data)
                  conflicts += "\nWydarzenie \"" + conflict.title + "\" w sali "
                      + conflict.room + " od " + conflict.start + " do " + conflict.end;

                that.error_message = "Nie udało się utworzyć wydarzenia. Nastąpiły konflikty z:" + conflicts;
              }
              else // otherwise some term is not filled completely
                that.error_message = "Któryś z termów jest nieuzupełniony.";
            }
          });
    },

    check_inputs_and_add_to_db: function () {
      if (this.check_inputs())
        this.add_to_db();
    },

    // Send edited reservation's data in POST
    edit_in_db: async function () {
      // If user who is not an admin tries to edit an event, its status has to be
      // changed to "pending" - otherwise unprivileged users would not be able to
      // edit events created by them.
      let that = this;
      await axios.post(this.url, {
        "title": this.name,
        "description": this.description,
        "visible": this.visible,
        "status": this.user_info.is_admin ? this.status : "0",
        "type": this.type,
        "terms": this.terms
      })
          .then(function (response) {
            that.hide_modal();
          })
          .catch(function (error) {
            that.show_alert = true;
            if (error.response.status == 400) {
              if (Array.isArray(error.response.data) && error.response.data.length) {
                // returned JSON with conflicts
                let conflicts = "";
                for (const conflict of error.response.data)
                  conflicts += "\nWydarzenie \"" + conflict.title + "\" w sali "
                      + conflict.room + " od " + conflict.start + " do " + conflict.end;

                that.error_message = "Nie udało się utworzyć wydarzenia. Nastąpiły konflikty z:" + conflicts;
              }
              else // otherwise some term is not filled completely
                that.error_message = "Któryś z termów jest nieuzupełniony.";
            }
          });
    },

    check_inputs_and_edit_in_db: function () {
      if (this.check_inputs())
        this.edit_in_db();
    },

    // Remove event with given URL from database
    remove_from_db: async function (url) {
      if (!url)
        return;

      await axios.post('delete-event/' + parseInt(url.match(/\d+/)) + '/');
      this.hide_modal();
    },
  }
}
</script>

<style scoped>
.dropdown-item.term.active {
  background: #2aabd2;
}

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

.term {
  height: 100px;
}

.term-bar {
  z-index: 1;
}

.term-free {
  z-index: 2;
  width: 100%;
  margin-top: -14px;
  visibility: hidden;
}

.term-occupied {
  z-index: 3;
  width: 100%;
  margin-top: -14px;
  visibility: hidden;
}

.alert-message {
  white-space: pre;
}

select[multiple] {
  height: 35px !important;
  transition: height 0.5s;
}

select[multiple]:focus {
  height: 120px !important;
}

</style>