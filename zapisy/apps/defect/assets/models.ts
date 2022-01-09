export interface DefectInfo {
    id: number,
    name: string,
    creation_date: Date,
    last_modification: Date,
    place: string,
    state: State,
    status_color: string
}

export type State = "Stworzone" | "Nie da się" | "Dłuższy problem" | "Zrobione"
