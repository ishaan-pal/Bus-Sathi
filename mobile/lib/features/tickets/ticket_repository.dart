import '../../core/api/api_client.dart';
import '../../core/models/ticket_model.dart';

class TicketRepository {
  TicketRepository(this._api);

  final ApiClient _api;

  Future<FareBreakdownModel> calculateFare({
    required String routeId,
    required String boardingStop,
    required String destinationStop,
    int adultCount = 1,
    int childCount = 0,
    int seniorCount = 0,
  }) async {
    final response = await _api.post<Map<String, dynamic>>(
      '/tickets/fare/calculate',
      data: {
        'route_id': routeId,
        'boarding_stop': boardingStop,
        'destination_stop': destinationStop,
        'adult_count': adultCount,
        'child_count': childCount,
        'senior_count': seniorCount,
      },
    );
    return FareBreakdownModel.fromJson(
      response.data!['fare'] as Map<String, dynamic>,
    );
  }

  Future<BookingInitiatedModel> bookTicket({
    required String busId,
    required String boardingStop,
    required String destinationStop,
    int adultCount = 1,
    int childCount = 0,
    int seniorCount = 0,
  }) async {
    final response = await _api.post<Map<String, dynamic>>(
      '/tickets/book',
      data: {
        'bus_id': busId,
        'boarding_stop': boardingStop,
        'destination_stop': destinationStop,
        'adult_count': adultCount,
        'child_count': childCount,
        'senior_count': seniorCount,
      },
    );
    return BookingInitiatedModel.fromJson(response.data!);
  }

  Future<void> confirmPayment({
    required String ticketId,
    String paymentId = 'demo_payment',
    String razorpaySignature = 'demo_signature',
  }) async {
    await _api.post<Map<String, dynamic>>(
      '/tickets/confirm-payment',
      data: {
        'ticket_id': ticketId,
        'payment_id': paymentId,
        'razorpay_signature': razorpaySignature,
      },
    );
  }

  Future<List<ActiveTicketModel>> getActiveTickets() async {
    final response = await _api.get<Map<String, dynamic>>('/tickets/active');
    final tickets = response.data?['tickets'] as List<dynamic>? ?? [];
    return tickets
        .map((e) => ActiveTicketModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<TicketDetailModel> getTicketDetail(String ticketId) async {
    final response =
        await _api.get<Map<String, dynamic>>('/tickets/$ticketId');
    return TicketDetailModel.fromJson(response.data!);
  }

  Future<String> refreshVerificationToken(String ticketId) async {
    final response = await _api.post<Map<String, dynamic>>(
      '/tickets/$ticketId/refresh-token',
    );
    return response.data!['verification_token'] as String;
  }
}
