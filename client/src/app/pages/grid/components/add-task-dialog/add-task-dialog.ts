import { Component, EventEmitter, inject, Output } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { DialogModule } from 'primeng/dialog';
import { FluidModule } from 'primeng/fluid';
import { InputTextModule } from 'primeng/inputtext';
import { CheckboxModule } from 'primeng/checkbox';

@Component({
  selector: 'app-add-task-dialog',
  standalone: true,
  imports: [DialogModule, ReactiveFormsModule, ButtonModule, FluidModule, InputTextModule, CheckboxModule],
  templateUrl: './add-task-dialog.html',
})
export class AddTaskDialog {
  public visible = true;
  @Output() public submitted = new EventEmitter<typeof this.form.value>();
  @Output() public cancelled = new EventEmitter<void>();

  protected fb = inject(FormBuilder);
  public form = this.fb.nonNullable.group({
    title: ['', Validators.required],
  });

  public submit() {
    if (this.form.valid) {
      this.submitted.emit(this.form.value);
    }
  }

  public cancel() {
    this.cancelled.emit();
  }
}
