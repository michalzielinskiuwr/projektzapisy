<script lang="ts">
// import {cloneDeep, sortBy, toPairs} from "lodash";
import Vue from "vue";

import TextFilter from "@/enrollment/timetable/assets/components/filters/TextFilter.vue";
import LabelsFilter from "@/enrollment/timetable/assets/components/filters/LabelsFilter.vue";
import SelectFilter from "@/enrollment/timetable/assets/components/filters/SelectFilter.vue";
import CheckFilter from "@/enrollment/timetable/assets/components/filters/CheckFilter.vue";
// import { DefectInfo } from "./models.ts"

export default Vue.extend({
  components: {
    TextFilter,
    LabelsFilter,
    SelectFilter,
    CheckFilter,
  },
  data: function () {
    return {
    };
  },
  created: function () {
    this.allStates = { 0: "Stworzone", 1: "Nie da się", 2: "Dłuższy problem", 3: "Zrobione"}
  },
});
</script>


<template>
  <div class="card bg-light">
    <div class="card-body">
      <div class="row">
        <div class="col">
          <TextFilter
            filterKey="name-filter"
            property="name"
            placeholder="Nazwa usterki"
          />
        </div>
        <div class="col">
          <LabelsFilter
            title="Stany"
            filterKey="state-filter"
            property="state"
            :allLabels="allStates"
            onClass="badge-success"
          />
          </div>
        <div class="col">
          <SelectFilter
            filterKey="place-filter"
            property="place"
            placeholder="Miejsce usterki"
          />
          </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.collapsed {
  overflow-y: hidden;
  height: 120px;

  // Blurs over the bottom of filter card.
  &:after {
    position: absolute;
    display: block;
    // Height of the card footer.
    bottom: 28px;
    left: 0;
    height: 50%;
    width: 100%;
    content: "";
    // Bootstrap light colour.
    background: linear-gradient(
      to top,
      rgba(248, 249, 250, 1) 0%,
      rgba(248, 249, 250, 0) 100%
    );
    pointer-events: none; /* so the text is still selectable */
  }
}

// Follows the Bootstrap 4 media query breakpoint.
@media (max-width: 767px) {
  .col-md + .col-md {
    border-top: 1px solid rgba(0, 0, 0, 0.1);
    padding-top: 1em;
  }
}

.card-footer {
  height: 28px;
}
</style>
