import { HttpEvent, HttpHandler, HttpInterceptor, HttpRequest } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { Environment, ENVIRONMENT } from 'vas-shared';
@Injectable()
export class AppInterceptorService implements HttpInterceptor {
  protected environment = inject<Environment>(ENVIRONMENT);
  public intercept(request: HttpRequest<unknown>, next: HttpHandler): Observable<HttpEvent<unknown>> {
    return next.handle(this.getRequest(request));
  }

  protected getRequest(request: HttpRequest<unknown>) {
    return request.clone({
      url: `${this.environment.baseUrl}/${request.url}`,
    });
  }
}
